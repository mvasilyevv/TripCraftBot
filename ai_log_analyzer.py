from together import Together


def extract_last_error_context(log_path, context_lines=5):
    with open(log_path, encoding="utf-8") as f:
        lines = f.readlines()
    for i in range(len(lines) - 1, -1, -1):
        if "error" in lines[i].lower() or "exception" in lines[i].lower():
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)
            return "".join(lines[start:end])
    return None


client = Together(api_key=os.getenv("TOGETHER_AI_TOKEN"))

log_fragment = extract_last_error_context("logs/app.log")
if not log_fragment:
    print("Ошибок в логе не найдено.")
else:
    prompt = (
        "Вот фрагмент лога с последней ошибкой:\n\n"
        f"{log_fragment}\n\n"
        "Прокомментируй причину ошибки и предложи пути её устранения."
    )
    completion = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    print("Комментарий AI по ошибке:\n")
    print(completion.choices[0].message.content)
