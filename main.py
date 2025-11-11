from collections import UserDict
from datetime import datetime, timedelta
import pickle
import os



class Field:

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):

    def __init__(self, value):
        if not (value.isdigit() and len(value) == 10):
            raise ValueError("Phone number must be 10 digits.")
        super().__init__(value)


class Birthday(Field):

    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY.")


# ---------- КЛАС ЗАПИСУ КОНТАКТУ ----------

class Record:

    def __init__(self, name): #Описує один контакт користувача 
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_value): #Додає новий телефон до контакту
        phone = Phone(phone_value)
        self.phones.append(phone)

    def edit_phone(self, old_value, new_value): #Змінює існуючий телефон
        for i, phone in enumerate(self.phones):
            if phone.value == old_value:
                self.phones[i] = Phone(new_value)
                return
        raise ValueError(f"Old phone {old_value} not found for {self.name.value}")

    def add_birthday(self, birthday_value): #Додає день народження для контакту
        self.birthday = Birthday(birthday_value)

    def __str__(self): #Форматує інформацію про контакт y зручний рядок.
        phones_str = "; ".join(p.value for p in self.phones) if self.phones else "No phones"
        birthday_str = self.birthday.value.strftime("%d.%m.%Y") if self.birthday else "N/A"
        return f"{self.name.value}: {phones_str}, Birthday: {birthday_str}"



class AddressBook(UserDict):
    #Колекція всіх контактів (словник з іменами як ключами)

    def add_record(self, record): #Додає новий запис (Record) до книги
        self.data[record.name.value] = record

    def find(self, name): #Повертає запис за іменем або None, якщо не знайдено
        return self.data.get(name)

    def delete(self, name): #Видаляє контакт за ім
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self): #Шукає користувачів y яких день народження припадає на найближчі 7 днів
        today = datetime.today().date()
        next_week = today + timedelta(days=7)
        upcoming = {}

        for record in self.data.values():
            if record.birthday:
                bday_this_year = record.birthday.value.replace(year=today.year)
                if bday_this_year < today:
                    bday_this_year = bday_this_year.replace(year=today.year + 1)
                if today <= bday_this_year <= next_week:
                    weekday = bday_this_year.strftime("%A")
                    upcoming.setdefault(weekday, []).append(record.name.value)

        if not upcoming:
            return "No birthdays in the next 7 days."

        result = ["Upcoming birthdays:"]
        for day, names in sorted(upcoming.items()):
            result.append(f"  {day}: {', '.join(names)}")
        return "\n".join(result)


# ---------- ДЕКОРАТОР ДЛЯ ОБРОБКИ ПОМИЛОК ----------

def input_error(func):
    """Декоратор, який ловить типові помилки користувача."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return f"{e}"
        except IndexError:
            return "Not enough arguments. Please check your input."
        except Exception as e:
            return f"Unexpected error: {e}"
    return wrapper


# ---------- ДОПОМІЖНІ ФУНКЦІЇ ДЛЯ КОМАНД ----------

def parse_input(user_input): #Розбиває введену користувачем команду на ключове слово та аргументи
    parts = user_input.strip().split()
    if not parts:
        return "", []
    cmd = parts[0].lower()
    args = parts[1:]
    return cmd, args


@input_error
def add_contact(args, book: AddressBook): #Додає новий контакт або телефон до існуючого
    if len(args) < 2:
        return "Command 'add' expects 2 arguments: <name: str> <phone: 10 digits>"
    name, phone = args[0], args[1]
    record = book.find(name)
    if not record:
        record = Record(name)
        book.add_record(record)
        msg = f"Contact '{name}' added."
    else:
        msg = f"Added new phone for {name}."
    record.add_phone(phone)
    return msg


@input_error
def change_contact(args, book: AddressBook): #Змінює старий номер телефону на новий
    if len(args) < 3:
        return "Command 'change' expects 3 arguments: <name> <old_phone> <new_phone>"
    name, old_phone, new_phone = args
    record = book.find(name)
    if not record:
        return f"Contact '{name}' not found. Use 'add {name} <phone>' first."
    record.edit_phone(old_phone, new_phone)
    return f"Phone for {name} updated."


@input_error
def show_phone(args, book: AddressBook): #Показує телефони користувача
    if len(args) < 1:
        return "Command 'phone' expects 1 argument: <name>"
    name = args[0]
    record = book.find(name)
    if not record:
        return f"Contact '{name}' not found."
    phones = ", ".join(p.value for p in record.phones) if record.phones else "No phones"
    return f"{name}: {phones}"


@input_error
def show_all(args, book: AddressBook):
    """Виводить усі контакти в адресній книзі."""
    if not book.data:
        return "Address book is empty."
    return "\n".join(str(record) for record in book.data.values())


@input_error
def add_birthday(args, book: AddressBook):
    """Додає день народження до існуючого контакту."""
    if len(args) < 2:
        return "Command 'add-birthday' expects 2 arguments: <name> <birthday: DD.MM.YYYY>"
    name, date_str = args
    record = book.find(name)
    if not record:
        return f"Contact '{name}' not found. Add it first with 'add {name} <phone>'."
    record.add_birthday(date_str)
    return f"Birthday added for {name}."


@input_error
def show_birthday(args, book: AddressBook):
    """Показує день народження користувача."""
    if len(args) < 1:
        return "Command 'show-birthday' expects 1 argument: <name>"
    name = args[0]
    record = book.find(name)
    if not record:
        return f"Contact '{name}' not found."
    if record.birthday:
        return f"{name}'s birthday: {record.birthday.value.strftime('%d.%m.%Y')}"
    return f"No birthday set for {name}."


@input_error
def birthdays(args, book: AddressBook):
    """Показує всі дні народження, які будуть протягом 7 днів."""
    return book.get_upcoming_birthdays()


# ---------- ФУНКЦІЇ ЗБЕРЕЖЕННЯ ТА ВІДНОВЛЕННЯ ----------

def save_data(book, filename="addressbook.pkl"): #Зберігає адресну книгу у файл за допомогою pickle   
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"): #Завантажує адресну книгу з файлу, якщо він існує
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            return pickle.load(f)
    return AddressBook()




def main():
    book = load_data()  # Відновлення книги при запуску
    print("Welcome to your assistant bot!")

    while True:
        user_input = input("\nEnter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)  # Збереження перед виходом
            print("Address book saved. Goodbye!")
            break

        elif command == "hello":
            print("Hi! How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "
