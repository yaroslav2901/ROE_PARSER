# 📘 Git & GitHub - Повна інструкція
## Правильний workflow для Python проєктів

---

## 1️⃣ Вимоги

- Linux (Debian / Ubuntu)
- Git встановлений: `sudo apt install git`
- Python 3.10+
- GitHub акаунт
- SSH-доступ до GitHub

---

## 2️⃣ Підготовка проєкту

```bash
cd ~/bots/PROJECT_NAME
ls -la  # перевірити всі файли
pwd     # переконатись що в правильній папці
```

---

## 3️⃣ Ініціалізація Git

```bash
git init
git branch -M main
git status
```

**Що відбувається:**
- `git init` – створює локальний репозиторій
- `git branch -M main` – перейменовує гілку на main
- `git status` – показує стан файлів

---

## 4️⃣ .gitignore (ОБОВ'ЯЗКОВО!)

**Створити файл ПЕРЕД першим комітом:**

```bash
nano .gitignore
```

**Вміст .gitignore:**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
env/
ENV/
*.egg-info/

# Проєкт
in/
out/
logs/
DEBUG_IMAGES/
debug_images/
temp/
tmp/

# Секретні дані
.env
*.env
config.ini
secrets.json

# Telegram
*.session
*.session-journal

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
```

---

## 5️⃣ Перший коміт

```bash
git add .
git status  # перевірити що додається
git commit -m "Initial commit: project structure"
```

**⚠️ Перевірте перед комітом:**
- Немає `.env` файлів
- Немає `.session` файлів
- Немає особистих даних в `in/` або `out/`

---

## 6️⃣ Створення репозиторію на GitHub

1. Відкрити https://github.com/new
2. **Repository name:** PROJECT_NAME
3. **Description:** (опціонально) "Parser for..."
4. **Public** або **Private**
5. **НЕ додавайте:**
   - ❌ README
   - ❌ .gitignore
   - ❌ License
6. Натиснути **Create repository**

---

## 7️⃣ SSH налаштування (один раз назавжди)

### Перевірка чи вже є ключ:

```bash
ls -la ~/.ssh/
```

### Якщо немає ключа:

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# Натискати Enter (використати defaults)
```

### Скопіювати публічний ключ:

```bash
cat ~/.ssh/id_ed25519.pub
```

### Додати на GitHub:

1. GitHub → Settings → SSH and GPG keys
2. New SSH key
3. Вставити ключ
4. Add SSH key

### Перевірка:

```bash
ssh -T git@github.com
# Має вивести: "Hi USERNAME! You've successfully authenticated..."
```

---

## 8️⃣ Підключення remote

```bash
git remote add origin git@github.com:USERNAME/PROJECT_NAME.git
git remote -v  # перевірити
```

**Має вивести:**
```
origin  git@github.com:USERNAME/PROJECT_NAME.git (fetch)
origin  git@github.com:USERNAME/PROJECT_NAME.git (push)
```

---

## 9️⃣ Перший pull (синхронізація)

```bash
git pull --rebase origin main
```

**Можливі результати:**
- `Already up to date` – все ок
- Конфлікти – вирішити вручну

---

## 🔟 Перший push

```bash
git push -u origin main
```

**Прапорець `-u`:**
- Встановлює upstream
- Наступні push будуть простіше

**Перевірка:** Оновити сторінку GitHub – файли мають з'явитись

---

## 🔄 Робочий цикл (щоденна робота)

### Додати нові зміни:

```bash
git add .                          # додати всі файли
git add file1.py file2.py          # або конкретні файли
```

### Зробити коміт:

```bash
git commit -m "Опис що зроблено"
```

**Приклади хороших комітів:**
```bash
git commit -m "Add error handling for API timeouts"
git commit -m "Fix parser crash on empty response"
git commit -m "Update .gitignore - exclude debug files"
```

### Синхронізувати з GitHub:

```bash
git pull --rebase origin main      # отримати зміни
git push                           # відправити свої зміни
```

---

## 🆘 Вирішення проблем

### Помилка: "remote origin already exists"

```bash
git remote remove origin
git remote add origin git@github.com:USERNAME/PROJECT_NAME.git
```

### Помилка: "Permission denied (publickey)"

```bash
# Перевірити SSH
ssh -T git@github.com

# Якщо не працює - переробити ключ
ssh-keygen -t ed25519 -C "your_email@example.com"
cat ~/.ssh/id_ed25519.pub
# Додати на GitHub знову
```

### Випадково закомітили .env

```bash
# Видалити з git, але залишити локально
git rm --cached .env
git commit -m "Remove .env from tracking"

# Додати в .gitignore якщо ще немає
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Add .env to .gitignore"
git push
```

### Конфлікт при pull

```bash
git pull --rebase origin main
# Якщо конфлікт:
# 1. Відкрити файл з конфліктом
# 2. Видалити маркери <<<< ==== >>>>
# 3. Зберегти правильну версію
git add .
git rebase --continue
```

### Скасувати останній коміт (якщо НЕ запушили)

```bash
git reset --soft HEAD~1   # залишити зміни staged
git reset HEAD~1          # залишити зміни unstaged
git reset --hard HEAD~1   # видалити зміни повністю (ОБЕРЕЖНО!)
```

---

## 📊 Корисні команди

### Перевірка стану:

```bash
git status              # що змінено
git log --oneline -5    # останні 5 комітів
git diff                # що змінено в файлах
git diff origin/main    # відмінності з GitHub
```

### Робота з гілками:

```bash
git branch              # список гілок
git branch feature-x    # створити нову гілку
git checkout feature-x  # перейти на гілку
git checkout main       # повернутись на main
```

### Очистка:

```bash
git clean -n            # показати що буде видалено
git clean -fd           # видалити untracked файли
```

---

## 🔐 Безпека - ЩО НІКОЛИ НЕ КОМІТИТИ

❌ **НІКОЛИ:**
- `.env` файли з паролями/токенами
- `*.session` файли Telegram
- API ключі в коді
- Паролі від БД
- Приватні ключі
- Особисті дані користувачів з `in/` або `out/`

✅ **НАТОМІСТЬ:**
- Використовувати `.env` + `.gitignore`
- Створити `.env.example` з прикладами
- Документувати які змінні потрібні в README

---

## 📝 Шаблон README.md

**Створити файл:**

```bash
nano README.md
```

**Приклад:**

```markdown
# Назва Проєкту

Короткий опис що робить парсер/бот.

## Встановлення

```bash
git clone git@github.com:USERNAME/PROJECT_NAME.git
cd PROJECT_NAME
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Налаштування

Створити `.env` файл:

```
API_KEY=your_key_here
DATABASE_URL=your_url_here
```

## Запуск

```bash
python main.py
```

## Автор

Ярослав Цибульський
```

---

## 🚀 Швидка довідка

```bash
# Щоденна робота
git add .
git commit -m "Опис змін"
git pull --rebase origin main
git push

# Перевірка
git status
git log --oneline -5
git diff

# Екстрені випадки
git reset --soft HEAD~1     # скасувати коміт
git rm --cached file.txt    # видалити з git
git clean -fd               # очистити untracked
```

---

## 📚 Додаткові ресурси

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Oh Shit, Git!?!](https://ohshitgit.com/) - вирішення проблем

---

**Автор:** Ярослав Цибульський  
**Версія:** 2.0  
**Дата:** Січень 2026