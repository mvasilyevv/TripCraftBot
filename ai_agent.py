import os

import ollama
import subprocess
import re
import ast
import sys
from pathlib import Path

from together import Together

README_SECTION_HEADER = "## AI-INSTRUCTIONS"
README_PATH = "README.md"
TEST_COMMAND = ["pytest", "--tb=short", "--maxfail=3"]

client = Together(api_key=os.getenv("TOGETHER_AI_TOKEN"))

def extract_clean_dict(llm_output):
    try:
        last_open = llm_output.rfind('{')
        last_close = llm_output.rfind('}')

        if last_open == -1 or last_close == -1 or last_close < last_open:
            raise ValueError("❌ Не удалось найти корректный словарь в ответе.")

        dict_text = llm_output[last_open:last_close + 1]

        parsed_dict = ast.literal_eval(dict_text)

        if not isinstance(parsed_dict, dict):
            raise ValueError("⚠️ Извлечённый блок не является словарём.")

        return parsed_dict

    except Exception as e:
        print(f"❌ Ошибка при извлечении словаря: {e}")
        print(f"🔎 Исходный ответ от LLM:\n{llm_output}")
        sys.exit(1)


def get_readme_section():
    if not Path(README_PATH).exists():
        print("❌ README.md не найден.")
        sys.exit(1)

    with open(README_PATH, encoding="utf-8") as f:
        content = f.read()

    match = re.search(rf"{README_SECTION_HEADER}\n(.*?)(\n## |\Z)", content, re.DOTALL)
    if not match:
        print("❌ Секция AI-INSTRUCTIONS не найдена в README.md")
        sys.exit(1)

    return match.group(1).strip()


def ask_llm(prompt: str) -> str:
    completion = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content


def run_command(command, description):
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(
            command, check=True, text=True,
            capture_output=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка во время: {description}")
        print(e.stdout)
        comment = ask_llm(f"Вот ошибка:\n{e.stdout}\n\nПоясни, что это значит и как её устранить.")
        print(f"💡 Комментарий от AI:\n{comment}")
        return False, e


def main():
    print("🤖 AI Агент запускается...")

    instructions = get_readme_section()
    print("📄 Инструкции из README.md:")
    print(instructions)

    llm_test_cmd = ask_llm(f"""
        Вот инструкции из README.md:
    
        {instructions}
    
        
        Сгенерируй Python-словарь, где:
        - ключ: bash-команда для тестирования,
        - значение: короткое описание этой команды.
        
        Твой ответ должен быть **только** в виде Python-кода внутри блока тройных кавычек. Без комментариев, размышлений, "<think>" и прочего.
    """)

    try:
        commands_dict = extract_clean_dict(llm_test_cmd)
    except Exception as e:
        print(f"❌ Ошибка при разборе ответа от LLM: {e}")
        print(f"Ответ был:\n{llm_test_cmd}")
        sys.exit(1)

    for cmd, desc in commands_dict.items():
        print(f"📦 Команда: {cmd}\n🔍 Описание: {desc}")
        success, _ = run_command(cmd.split(), desc)
        if not success:
            print("🛑 Команда завершилась с ошибкой. Прекращаю выполнение.")
            return

    print("🎉 Деплой завершён успешно.")


if __name__ == "__main__":
    main()