import json

file_path = "words.json"

# Загружаем данные
with open(file_path, "r", encoding="utf-8") as f:
    words = json.load(f)

original_count = len(words)

# Убираем дубликаты по полю "word"
seen = set()
unique_words = []
for w in words:
    if w["word"] not in seen:
        unique_words.append(w)
        seen.add(w["word"])

removed_count = original_count - len(unique_words)

# Сохраняем в формате: одна строка на слово
with open(file_path, "w", encoding="utf-8") as f:
    f.write("[\n")
    for i, w in enumerate(unique_words):
        json_str = json.dumps(w, ensure_ascii=False, separators=(",", ":"))
        if i < len(unique_words) - 1:
            f.write(f"{json_str},\n")
        else:
            f.write(f"{json_str}\n")
    f.write("]")

# Выводим результат
print(f"Всего слов было: {original_count}")
print(f"Удалено повторов: {removed_count}")
print(f"Осталось слов: {len(unique_words)}")