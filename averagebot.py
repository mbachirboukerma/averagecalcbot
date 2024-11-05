from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from retrying import retry
from telegram.error import TimedOut, Unauthorized
import sqlite3
from contextlib import closing
import logging
import math

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize database
def init_db():
    with closing(sqlite3.connect("bot_data.db")) as conn:
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS visitors (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER UNIQUE)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS overall_average_count (count INTEGER)''')
            conn.execute('''INSERT OR IGNORE INTO overall_average_count (count) VALUES (0)''')

# Update visitor count
def update_visitors(user_id):
    with closing(sqlite3.connect("bot_data.db")) as conn:
        with conn:
            conn.execute("INSERT OR IGNORE INTO visitors (user_id) VALUES (?)", (user_id,))

# Get visitor count
def get_visitor_count():
    with closing(sqlite3.connect("bot_data.db")) as conn:
        with conn:
            count = conn.execute("SELECT COUNT(*) FROM visitors").fetchone()[0]
    return count

# Get all user IDs
def get_all_user_ids():
    with closing(sqlite3.connect("bot_data.db")) as conn:
        with conn:
            user_ids = conn.execute("SELECT user_id FROM visitors").fetchall()
    return [user_id[0] for user_id in user_ids]

# Get overall average count
def get_overall_average_count():
    with closing(sqlite3.connect("bot_data.db")) as conn:
        with conn:
            count = conn.execute("SELECT count FROM overall_average_count").fetchone()[0]
    return count

# Increment overall average count
def increment_overall_average_count():
    with closing(sqlite3.connect("bot_data.db")) as conn:
        with conn:
            conn.execute("UPDATE overall_average_count SET count = count + 1")

# Function to remove user from the database
def remove_user_from_database(user_id):
    with closing(sqlite3.connect("bot_data.db")) as conn:
        with conn:
            conn.execute("DELETE FROM visitors WHERE user_id = ?", (user_id,))
        logging.info(f"Removed user {user_id} from database")

# Function to send a message and handle Unauthorized error
def send_message(bot, chat_id, text):
    try:
        bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
    except Unauthorized as e:
        logging.warning(f"Failed to send message to {chat_id}: {e}")
        remove_user_from_database(chat_id)
    except Exception as e:
        logging.error(f"Failed to send message to {chat_id}: {e}")

# Notify all users that the bot is online

MESSAGE = (
    "<b>The bot is online now ❤️😁 </b>.\n"
    "<b>يرجى ملاحظة أن البوت قد يتوقف أحيانًا بسبب أن الاستضافة مجانية.</b>\n"
    "<b>إذا واجهتم أي مشكلة في عمل البوت، لا تترددوا في مراسلتي على الخاص لإعادة تشغيله.</b>\n"
    "<b>@yassineboukerma</b>"
)


def notify_users(context: CallbackContext):
    user_ids = get_all_user_ids()
    for user_id in user_ids:
        try:
            context.bot.send_message(chat_id=user_id, text=MESSAGE, parse_mode='HTML')
           # context.bot.send_message(chat_id=user_id, text=MESSAGE_AR, parse_mode='HTML')
        except Unauthorized as e:
            logging.warning(f"Failed to send message to {user_id}: {e}")
            remove_user_from_database(user_id)
        except Exception as e:
            logging.error(f"Failed to send message to {user_id}: {e}")

#whats new messages

MESSAGE_whatsnew = (
    "🎉 <b>New Patch Released!</b> 🎉\n\n"
    "Hello everyone! We're excited to announce a new update to the Grade Calculator Bot. Here's what's new:\n\n"
    "1. <b>We have added new levels</b>:Physics3 (+4), Science3 (+4) , science3 (+5), Math - Fourth Year (+5) and Sciences - Second Year.\n"
    "2. <b>Visitor Count</b>: You can now see how many unique users have visited the bot with the command /visitor_count.\n"
    "3. <b>Usage Count</b>: You can now see how many times the Bot has been used with the command /usage_count.\n\n"
    "4. <b>Bug Fixes</b>: We've fixed several bugs to improve the overall user experience.\n"
    "5. <b>Improved Help</b>: Need assistance? Just type /help for detailed instructions.\n"
    "6. <b>Enhanced Validations</b>: Better input validation to ensure accurate grade calculations.\n\n"
    "Update Date: <b>19 June 2024</b>\n\n"
    "Thank you for using our bot! If you have any questions or need further assistance, feel free to reach out.\n\n"
    "Happy calculating! 📊"
)

MESSAGE_AR_whatsnew = (
    "🎉 <b>تحديث جديد تم إصداره!</b> 🎉\n\n"
    "مرحبًا بالجميع! نحن متحمسون للإعلان عن تحديث جديد لبوت حساب المعدل بالنسبة لجميع التخصصات بالمدرسة العليا للأساتذة _ القبة. إليكم ما هو جديد:\n\n"
    "1. <b>مستويات جديدة</b>: لقد أضفنا المستويات: فيزياء - السنة الثالثة (+4)، علوم - السنة الثالثة (+4)، علوم - السنة الثالثة (+5)، الرياضيات - السنة الرابعة (+5) وعلوم - السنة الثانية.\n"
    "2. <b>عدد الزوار</b>: يمكنك الآن رؤية عدد المستخدمين الذين زاروا الروبوت باستخدام الأمر /visitor_count.\n"
    "3. <b>عدد مرات الاستخدام</b>: يمكنك الآن معرفة عدد المرات التي تم فيها استعمال البوت باستخدام الأمر /usage_count.\n\n"
    "4. <b>تصحيح بعض الأخطاء</b>: لقد قمنا بتصحيح العديد من الأخطاء لتحسين تجربة المستخدم العامة.\n"
    "5. <b>تحسين المساعدة</b>: تحتاج إلى مساعدة؟ فقط اكتب /help للحصول على تعليمات مفصلة.\n"
    "6. <b>تحسين التحقق من المدخلات</b>: تحقق أفضل من العلامات لضمان حساب دقيق للمعدلات.\n\n"
    "تاريخ التحديث: <b>19 يونيو 2024</b>\n\n"
    "شكرًا لاستخدامك البوت الخاص بنا! إذا كانت لديك أي أسئلة أو إستفسارات، يرجى التواصل معنا، نحن في الخدمة دائما.\n\n"
    "تجربة ممتعة! 😊"
)


# Define specialization choices
SPECIALIZATION, LEVEL, SUB_LEVEL, FIRST, SECOND, TP, TD, NEXT_SUBJECT = range(8)

# Define groups for exams, TD, and TP
exam1_subjects = [
    "analyse", "informatiquee", "algebre", "thermo", "stm", "mecanique", "elect", "tarikh l3olom", "tarbiya","solid_state_physics","organic_chemistry","analytical_chemistry","technological_measurements","modern_physics",
    "topologie", "analyse 2", "calculs différentiels", "informatique", "psychologie 'enfant'", "psycho éducative", "Mécanique quantique", "méthodes math", "thermochimie", "9iyassat",
    "géométrie", "algèbre linéaire", "algèbre générale", "analyse numérique", "analyse complexe", "algèbre3",
    "théorie de mesure و de l’intégration1", "psychologie éducative", "statistiques و probabilités", "logique",
    "math", "Optique", "Cinetique && électrochimie", "équilibre", "électronique", "algo","physics_education",
    "sm1", "logique", "électro", "stat", "education sciences 'fares'", "français", "algo2", "sm2", "se 1", "si 1",
    "thl", "ts", "psychologie 'fares'", "anglais", "réseau", "se 2", "compilation", "web", "ro", "psycho", "si 2", "ai", "chimie", "biophysique", "géologie","didactiques mathématiques", "Analyse complexe","Algèbre4", "Théorie de  mesure et de l'intégration2", "Géométrie", "Statistiques et probabilités2","Équations différentielles","Biochimie","Botanique","Zoologie","Microbiologie","Génétique","Paléontologie","physiologie_végétale","physiologie_animal","pétrologie","biomol","psycho3"
]
exam2_subjects = [
    "analyse", "informatiquee", "algebre", "thermo", "stm", "mecanique", "elect", "tarikh l3olom", "tarbiya","solid_state_physics","organic_chemistry","analytical_chemistry","technological_measurements","modern_physics",
    "topologie", "analyse 2", "calculs différentiels", "informatique", "psychologie 'enfant'",  "psycho éducative", "Mécanique quantique", "méthodes math", "thermochimie", "9iyassat",
    "géométrie", "algèbre linéaire", "algèbre générale", "analyse numérique", "analyse complexe", "algèbre3",
    "théorie de mesure و de l’intégration1", "psychologie éducative", "statistiques و probabilités", "logique",
    "math", "Cinetique && électrochimie", "équilibre", "électronique", "algo","education sciences 'fares'","physics_education",
    "sm1", "logique", "électro", "stat", "français", "algo2", "sm2", "se 1", "si 1",
    "thl", "ts", "psychologie 'fares'", "anglais", "réseau", "se 2", "compilation", "web", "ro", "psycho", "si 2", "ai", "chimie", "biophysique", "géologie","didactiques mathématiques", "Analyse complexe","Algèbre4", "Théorie de  mesure et de l'intégration2", "Géométrie", "Statistiques et probabilités2","Équations différentielles","Biochimie","Botanique","Zoologie","Microbiologie","Génétique","Paléontologie","physiologie_végétale","physiologie_animal","pétrologie","biomol","psycho3"
]

td_subjects = [
    "math", "vibrations", "psychologie 'fares'", "psychologie 'enfant'", "Optique", "Cinetique && électrochimie", "équilibre", "électronique", "informatique",
    "algo", "algo2", "sm1", "sm2", "stat", "se 1", "thl", "si 1", "ts", "analyse numérique", "psycho", "ro", "se 2", "compilation","mécanique classique", "nisbiya", "psycho éducative", "chimie organique", "chimie analytique", "Mécanique quantique", "méthodes math", "thermochimie", "9iyassat",
    "topologie", "analyse 2", "calculs différentiels", "géométrie", "algèbre linéaire", "algèbre générale", "analyse complexe","stm",
    "algèbre3", "théorie de mesure و de l’intégration1", "statistiques و probabilités", "analyse", "algebre", "thermo","solid_state_physics","organic_chemistry","physics_education","analytical_chemistry","chemistry_education","technological_measurements","modern_physics", "mecanique", "elect", "logique", "électro", "psychologie éducative", "chimie", "biophysique","didactiques mathématiques", "Analyse complexe","Algèbre4", "Théorie de  mesure et de l'intégration2", "Géométrie", "Statistiques et probabilités2","Équations différentielles","Biochimie","Zoologie","Génétique","Psycho2","biomol","psycho3"
]

tp_subjects = [
    "vibrations", "informatiquee", "Optique", "Cinetique && électrochimie", "équilibre", "électronique", "compilation", "web",
    "réseau", "algo2", "thermo", "stm", "mecanique", "elect", "algo", "cyto", "histo", "bv", "embryo", "géologie","Biochimie","Botanique","Zoologie","Microbiologie","Paléontologie","physiologie_végétale","physiologie_animal","pétrologie",
]

subject_with_cc =["chimie organique", "chimie analytique", "thermochimie", "9iyassat" ,"solid_state_physics", "organic_chemistry", "physics_education", "analytical_chemistry", "chemistry_education", "technological_measurements"]


# Define special subjects that require direct average input
special_subjects = ["vibrations", "Optique"]

# Define grades and coefficients for each specialization and level
specializations = {
    'math': {
        'math1': {
            "analyse": 4,
            "algebre": 2,
            "thermo": 3,
            "stm": 3,
            "mecanique": 3,
            "elect": 3,
            "tarikh l3olom": 1,
            "tarbiya": 1,
        },
        'math2': {
            "topologie": 4,
            "analyse 2": 2,
            "calculs différentiels": 2,
            "informatiquee": 2,
            "psychologie 'enfant'": 2,
            "géométrie": 2,
            "algèbre linéaire": 2,
            "algèbre générale": 2,
        },
        'math3': {
            "analyse numérique": 4,
            "analyse complexe": 2,
            "algèbre3": 2,
            "théorie de mesure و de l’intégration1": 2,
            "psychologie éducative": 2,
            "géométrie": 2,
            "statistiques و probabilités": 2,
            "logic math": 1,
        },
        'math4 (+4)': {},
        'math4 (+5)': {
            "didactiques mathématiques": 2,
            "Analyse complexe": 2,
            "Algèbre4": 2,
            "Théorie de  mesure et de l'intégration2": 2,
            "Programmes d'études": 1,
            "Géométrie": 2,
            "Statistiques et probabilités2": 2,
            "Équations différentielles": 2,
        },
        'math5': {}
    },
    'physics': {
        'physics1': {
            "analyse": 4,
            "algebre": 2,
            "thermo": 3,
            "stm": 3,
            "mecanique": 3,
            "elect": 3,
            "tarikh l3olom": 1,
            "tarbiya": 1,
        },
        'physics2': {
            "math": 4,
            "vibrations": 3,  # اهتزازات
            "Optique": 3,  # الضوء
            "Cinetique && électrochimie": 3,  # الكيمياء الحركية و الكهربائية
            "équilibre": 4,  # توازنات
            "électronique": 4,  # إلكترونيات
            "informatique": 2,  # معلوماتية
            "psycho": 2,  # علم النفس
        },
        'physics3 (+4)': {
            "solid_state_physics": 4,
            "modern_physics": 4,
            "organic_chemistry": 4,
            "physics_education": 4,
            "analytical_chemistry": 3,
            "chemistry_education": 2,
            "technological_measurements": 2,
            "psycho3": 2,
        },
        'physics3 (+5)': {
            "mécanique classique": 3,
            "nisbiya": 3,
            "psycho3": 2,
            "chimie organique": 3,
            "chimie analytique": 3,
            "Mécanique quantique": 3,
            "méthodes math": 3,
            "thermochimie": 3,
            "9iyassat": 2,
        },
        'physics4 (+4)': {},
        'physics4 (+5)': {},
        'physics5': {}
    },
    'info': {
        'info1': {
            "algo": 5,
            "sm1": 4,
            "logique": 3,
            "algebre": 3,
            "analyse": 3,
            "électro": 3,
            "stat": 2,
            "tarikh l3olom": 1,
            "education sciences 'fares'": 1,
            "français": 1
        },
        'info2': {
            "algo2": 5,
            "sm2": 4,
            "se 1": 4,
            "si 1": 3,
            "thl": 3,
            "ts": 3,
            "analyse numérique": 3,
            "psychologie 'fares'": 2,
            "anglais": 1
        },
        'info3': {
            "réseau": 4,
            "se 2": 4,
            "compilation": 4,
            "web": 3,
            "ro": 3,
            "psycho": 2,
            "si 2": 2,
            "ai": 2,
            "anglais": 1,
        },
        'info4 (+4)': {},
        'info4 (+5)':{},
        'info5': {}
    },
    'sciences': {
        'sciences1': {
            "chimie": 3,
            "biophysique": 3,
            "math": 3,
            "info": 1,
            "tarbya": 1,
            "cyto": 1.5,
            "histo": 1.5,
            "bv": 1.5,
            "embryo": 1.5,
            "géologie": 3,
        },
        'sciences2': {
            "Biochimie": 4,
            "Botanique": 4,
            "Zoologie": 4,
            "Microbiologie": 3,
            "Génétique": 3,
            "Paléontologie": 2,
            "Psycho2": 2,
        },
        'sciences3 (+4)': {
            "physiologie_animal": 3,
            "physiologie_végétale": 3,
            "biomol": 2,
            "pétrologie": 3,
            "psycho3": 2,
            "immunologie": 1,
            "parasitologie": 1,
            "anglais ": 1,
            "nutrition": 1,
        },
        'sciences3 (+5)': {
            "physiologie_animal": 3,
            "physiologie_végétale": 3,
            "biomol": 3,
            "pétrologie": 3,
            "psycho3": 2,
            "immunologie": 1,
            "parasitologie": 1,
            "anglais ": 1,
        },
        'sciences4 (+4)': {},
        'sciences4 (+5)':{},
        'sciences5': {}
    },
    'musique': {
        'musique1': {},
        'musique2': {},
        'musique3': {},
        'musique4 (+4)': {},
        'musique4 (+5)': {},
        'musique5': {}
    }
}

# Menu keyboard to appear after showing overall average
def get_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Visit our website", url='http://www.infotouch.tech')],
        [InlineKeyboardButton("Follow us on Instagram", url='http://www.instagram.com/infotouchclub')]
    ])

@retry(wait_fixed=2000, stop_max_attempt_number=5, retry_on_exception=lambda x: isinstance(x, TimedOut))
def start(update: Update, context: CallbackContext) -> int:
    # تسجيل الزائر الجديد
    user_id = update.message.from_user.id
    update_visitors(user_id)

    keyboard = [
        ["Math"],
        ["Physics"],
        ["Info"],
        ["Sciences"],
        ["Musique"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text(
        "Hello! Welcome to the Grade Calculator Bot. 🎓\n\n"
        "This bot will help you calculate your overall average grade. Please choose your specialization to get started:\n"
        "- Math\n"
        "- Physics\n"
        "- Info\n"
        "- Sciences\n"
        "- Musique\n\n"
        "If you need any help, type /help. To cancel the process at any time, type /cancel.",
        reply_markup=reply_markup,
    )
    return SPECIALIZATION

def choose_specialization(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    specialization = update.message.text.lower()

    if specialization not in specializations:
        update.message.reply_text("Please choose a valid specialization.")
        return SPECIALIZATION

    user_data['specialization'] = specialization
    keyboard = [[f"{specialization.capitalize()}1"], [f"{specialization.capitalize()}2"], [f"{specialization.capitalize()}3"], [f"{specialization.capitalize()}4"],[f"{specialization.capitalize()}5"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text("Please choose your level:", reply_markup=reply_markup)
    return LEVEL

levelsWithSubLevels = ["physics4", "math4", "sciences4", "info4","sciences3",'physics3']

def choose_level(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    level = update.message.text.lower()

    not_added_levels = [ "sciences4 (+4)", "sciences4 (+5)", "sciences5",
                    "physics4 (+4)", "physics4 (+5)", "physics5",
                    "math4 (+4)", "math5",
                    "info4 (+4)", "info4 (+5)", "info5"]
    not_supported_levels = ["musique1", "musique2", "musique3", "musique4 (+4)", "musique4 (+5)", "musique5"]

    if level in not_added_levels:
        update.message.reply_text("لم يتم اضافة هذا التخصص بعد، يرجى الانتظار.")
        update.message.reply_text("This level is not listed yet, Please wait for upcoming updates.")
        return ConversationHandler.END

    if level in not_supported_levels:
        update.message.reply_text("<b>هذا التخصص لن يتم دعمه.</b>", parse_mode='HTML')
        update.message.reply_text(
            "الحمد لله، والصلاة والسلام على رسول الله، وعلى آله، وصحبه، أما بعد:\n\n"
            "فالموسيقى لا تجوز دراستها، ولا تدريسها للكبار، ولا للصغار، وراجع في ذلك الفتاوى ذوات الأرقام التالية: "
            "<a href=\"https://www.islamweb.net/ar/fatwa/7932/%D9%87%D9%84-%D9%8A%D8%AC%D9%88%D8%B2-%D8%AD%D8%B6%D9%88%D8%B1-%D8%AF%D8%B1%D9%88%D8%B3-%D8%A7%D9%84%D9%85%D9%88%D8%B3%D9%8A%D9%82%D9%89-%D8%A5%D8%B0%D8%A7-%D8%AA%D9%88%D9%82%D9%81-%D8%B9%D9%84%D9%8A%D9%87%D8%A7-%D8%A7%D9%84%D8%AA%D8%AE%D8%B1%D8%AC\">7932</a>، "
            "<a href=\"https://www.islamweb.net/ar/fatwa/73834/%D8%AD%D9%83%D9%85-%D8%A7%D9%84%D8%AF%D8%B1%D8%A7%D8%B3%D8%A9-%D9%81%D9%8A-%D9%83%D9%84%D9%8A%D8%A9-%D9%85%D9%86-%D8%B6%D9%85%D9%86-%D9%85%D9%88%D8%A7%D8%AF%D9%87%D8%A7-%D8%A7%D9%84%D9%85%D9%88%D8%B3%D9%8A%D9%82%D9%89\">73834</a>، "
            "<a href=\"https://www.islamweb.net/ar/fatwa/191797/%D8%AD%D8%B1%D9%85%D8%A9-%D8%A7%D9%84%D9%85%D9%88%D8%B3%D9%8A%D9%82%D9%89-%D8%AA%D8%B4%D9%85%D9%84-%D8%AF%D8%B1%D8%A7%D8%B3%D8%AA%D9%87%D8%A7%D8%8C%20%D9%88%D9%84%D8%A7,%D8%AA%D8%AE%D9%84%D9%88%20%D9%85%D9%86%20%D9%85%D8%AB%D9%84%20%D9%87%D8%B0%D9%87%20%D8%A7%D9%84%D9%85%D8%A7%D8%AF%D8%A9.\">المصدر</a>"
        , parse_mode='HTML')
        return ConversationHandler.END

    specialization = user_data['specialization']
    if level in levelsWithSubLevels:
        user_data['level_base'] = level
        keyboard = [["+4"], ["+5"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        update.message.reply_text("Please choose your sub-level:", reply_markup=reply_markup)
        return SUB_LEVEL

    if level not in specializations[specialization]:
        update.message.reply_text("Please choose a valid level.")
        return LEVEL

    user_data['level'] = level
    user_data['current_subject_index'] = 0
    user_data['subject_grades'] = {}
    user_data['total_grades'] = 0
    user_data['total_coefficients'] = 0

    return ask_for_grades(update, context)

def choose_sub_level(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    sub_level = update.message.text.lower()
    not_added_levels = ["sciences4 (+4)", "sciences4 (+5)", "sciences5",
                    "physics4 (+4)", "physics4 (+5)", "physics5",
                    "math4 (+4)", "math5",
                    "info4 (+4)", "info4 (+5)", "info5"]
    if sub_level not in ["+4", "+5"]:
        update.message.reply_text("Please choose a valid sub-level.")
        return SUB_LEVEL

    level_base = user_data['level_base']
    if sub_level == "+4":
        if f"{level_base} (+4)" in not_added_levels:
            update.message.reply_text("لم يتم اضافة هذا التخصص بعد، يرجى الانتظار.")
            update.message.reply_text("This level is not listed yet, Please wait for upcoming updates.")
            return ConversationHandler.END
        user_data['level'] = f"{level_base} (+4)"
    elif sub_level == "+5":
        if f"{level_base} (+5)" in not_added_levels:
            update.message.reply_text("لم يتم اضافة هذا التخصص بعد، يرجى الانتظار.")
            update.message.reply_text("This level is not listed yet, Please wait for upcoming updates.")
            return ConversationHandler.END
        user_data['level'] = f"{level_base} (+5)"

    user_data['current_subject_index'] = 0
    user_data['subject_grades'] = {}
    user_data['total_grades'] = 0
    user_data['total_coefficients'] = 0

    return ask_for_grades(update, context)

def ask_for_grades(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    specialization = user_data['specialization']
    level = user_data['level']
    subjects = list(specializations[specialization][level].keys())
    current_index = user_data['current_subject_index']

    if current_index >= len(subjects):
        if user_data['total_coefficients'] == 0:
            update.message.reply_text("No subjects found for this level.")
            return ConversationHandler.END

        average = user_data['total_grades'] / user_data['total_coefficients']
        increment_overall_average_count()
        update.message.reply_text("<b>---------------------------------------------</b>", parse_mode='HTML')
        average = math.ceil(average * 100) / 100
        update.message.reply_text(f"<b>Your overall average grade is: <span class=\"tg-spoiler\">{average:.2f}</span></b>", parse_mode='HTML')

        if average >= 10.00:
            update.message.reply_text("<b><span class=\"tg-spoiler\">Congratulations!! YA LKHABACH</span></b>", parse_mode='HTML')
        else:
            update.message.reply_text("<b><span class=\"tg-spoiler\">Don't worry, Rana ga3 f rattrapage.</span></b>", parse_mode='HTML')

        update.message.reply_text(
            "<b>Thank you for using our bot</b>\n\n"
            "<b>Don't forget to follow us on Instagram and visit our website!!</b>\n\n"
            "<b>If you want to use the bot again, click /start.</b>\n\n\n"
            "<b>Developed by <a href=\"https://www.instagram.com/yassine_boukerma\">Yassine Boukerma</a> with ❤️</b>",
            reply_markup=get_menu_keyboard(),
            parse_mode='HTML'
        )

        return ConversationHandler.END

    subject = subjects[current_index]
    user_data['current_subject'] = subject
    user_data['current_subject_grades'] = []

    if subject in special_subjects:
        update.message.reply_text(f"Enter the average grade for {subject} directly:", parse_mode='HTML')
        return NEXT_SUBJECT

    update.message.reply_text(f"Enter the grade for {subject} - Exam 1 :", parse_mode='HTML')
    return FIRST

def validate_grade(grade: str) -> bool:
    try:
        value = float(grade)
        return 0 <= value <= 20
    except ValueError:
        return False

def receive_first_grade(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    grade = update.message.text

    if not validate_grade(grade):
        update.message.reply_text("Please enter a valid grade between 0 and 20.")
        return FIRST

    user_data['current_subject_grades'].append(float(grade))

    if user_data['current_subject'] in exam1_subjects:
        update.message.reply_text(f"Enter the grade for {user_data['current_subject']} - Exam 2 :", parse_mode='HTML')
        return SECOND
    else:
        return receive_second_grade(update, context)

def receive_second_grade(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    grade = update.message.text

    if not validate_grade(grade):
        update.message.reply_text("Please enter a valid grade between 0 and 20.")
        return SECOND

    if user_data['current_subject'] in exam2_subjects:
        user_data['current_subject_grades'].append(float(grade))
    else:
        user_data['current_subject_grades'].append(user_data['current_subject_grades'][0])

    if user_data['current_subject'] in tp_subjects:
        update.message.reply_text(f"Enter the grade for {user_data['current_subject']} - TP :", parse_mode='HTML')
        return TP
    else:
        return receive_tp_grade(update, context)

def receive_tp_grade(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    grade = update.message.text

    if user_data['current_subject'] in tp_subjects:
        if not validate_grade(grade):
            update.message.reply_text("Please enter a valid grade between 0 and 20.")
            return TP
        user_data['current_subject_grades'].append(float(grade))
    else:
        user_data['current_subject_grades'].append(None)

    if user_data['current_subject'] in (td_subjects and subject_with_cc):
        update.message.reply_text(f"Enter the grade for {user_data['current_subject']} - CC :", parse_mode='HTML')
        return TD
    elif user_data['current_subject'] in td_subjects:
        update.message.reply_text(f"Enter the grade for {user_data['current_subject']} - TD :", parse_mode='HTML')
        return TD
    else:
        return receive_td_grade(update, context)

def receive_td_grade(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    grade = update.message.text

    if user_data['current_subject'] in td_subjects:
        if not validate_grade(grade):
            update.message.reply_text("Please enter a valid grade between 0 and 20.")
            return TD
        user_data['current_subject_grades'].append(float(grade))
    else:
        user_data['current_subject_grades'].append(None)

    return calculate_subject_average(update, context)

def calculate_subject_average(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    specialization = user_data['specialization']
    level = user_data['level']
    subject = user_data['current_subject']
    grades = user_data['current_subject_grades']
    coefficient = specializations[specialization][level][subject]

    # Ensure there are no None values before summing
    grades = [grade for grade in grades if grade is not None]

    if specialization == 'sciences' and level == 'sciences1':
        if subject in ["chimie", "biophysique", "math"]:
            # TD + Exam1 + Exam2 / 3
            average = sum(grades[:3]) / 3
        elif subject == "géologie":
            # Exam1 + Exam2 + TP / 3
            average = sum(grades[:3]) / 3
        elif subject in ["cyto", "histo", "bv", "embryo"]:
            # 0.7 * Exam + 0.3 * TP
            average = 0.7 * grades[0] + 0.3 * grades[2]
            user_data['subject_grades'][subject] = average

            update.message.reply_text(
                f"<b>The average grade for {subject} is: {average:.2f}</b>",
                parse_mode='HTML'
            )

            if all(sub in user_data['subject_grades'] for sub in ["cyto", "histo", "bv", "embryo"]):
                # Calculate general biology average
                bio_average = sum(user_data['subject_grades'][sub] for sub in ["cyto", "histo", "bv", "embryo"]) / 4
                user_data['total_grades'] += bio_average * 6
                user_data['total_coefficients'] += 6
        else:
            # Single Exam subjects (info, tarbya)
            average = grades[0]

    elif specialization == 'sciences' and level == 'sciences2':
        if subject == "Génétique":
            # TD + Exam1 + Exam2 / 3
            average = sum(grades[:3]) / 3
        elif subject == "Psycho2":
            # Exam 1 *2 + TD / 3
            average = (grades[0]*2 + grades[2]) / 3
        elif subject in ["Botanique", "Microbiologie", "Paléontologie"]:
            # Exam1 + Exam2 + TP / 3
            average = sum(grades[:3]) / 3
        elif subject == "Zoologie":
            # (Exam1 + Exam2 + 0.5 * TP + 0.5 * TD) / 3
            average = (sum(grades[:2]) + (0.5 * grades[2] + 0.5 * grades[3])) / 3
        elif subject == "Biochimie":
            # (Exam1 + Exam2 + 0.75 * TP + 0.25 * TD) / 3
            average = (sum(grades[:2]) + (0.75 * grades[2] + 0.25 * grades[3])) / 3
        else:
            # Single Exam subjects (info, tarbya)
            average = grades[0]

    elif subject == "chemistry_education":
        average = (grades[0]*2 + grades[2])/3
    else:
        # Existing calculations for other specializations
        if len(grades) == 1:
            average = grades[0]
        elif len(grades) == 2:  # No TP or TD
            average = sum(grades) / 2
        elif len(grades) == 3:  # TP or TD only
            average = sum(grades) / 3
        elif len(grades) == 4:
            if (specialization == 'physics' and level == 'physics3 (+4)') or (specialization == 'info' and (level == 'info2' or level== 'info3')):
                # Exam1 + Exam2 + (TP * 0.5 + TD * 0.5) / 3
                average = (sum(grades[:2]) + (grades[2] * 0.5 + grades[3] * 0.5)) / 3
            else:
                # Both TP and TD
                average = (sum(grades[:2]) + (2 * grades[2] + grades[3]) / 3) / 3

    # Print the average grade for the current subject if not handled by the specific subjects block
    if subject not in ["cyto", "histo", "bv", "embryo"]:
        update.message.reply_text(
            f"<b>The average grade for {subject} is: {average:.2f}</b>",
            parse_mode='HTML'
        )

        user_data['total_grades'] += average * coefficient
        user_data['total_coefficients'] += coefficient

    user_data['current_subject_index'] += 1
    return ask_for_grades(update, context)

def receive_subject_average(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    subject = user_data['current_subject']
    average = update.message.text

    if not validate_grade(average):
        update.message.reply_text("Please enter a valid average between 0 and 20.")
        return NEXT_SUBJECT

    average = float(average)
    coefficient = specializations[user_data['specialization']][user_data['level']][subject]

    user_data['total_grades'] += average * coefficient
    user_data['total_coefficients'] += coefficient

    user_data['current_subject_index'] += 1
    return ask_for_grades(update, context)

def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "📚 <b>Here are the instructions:</b>\n\n"
        "1. Click <b>/start</b> to begin using the bot.\n"
        "2. Follow the prompts to enter your grades.\n"
        "3. Make sure to enter valid grades between 0 and 20.\n"
        "4. Click <b>/cancel</b> if you want to stop the bot.\n"
        "5. To restart, first click <b>/cancel</b> then <b>/start</b>.\n"
        "If you need further assistance, just text @yassineboukerma\n\n\n"
        "📚 <b>إليك التعليمات:</b>\n\n"
        "1. اضغط على <b>/start</b> للبدء في استعمال البوت.\n"
        "2. اتبع التعليمات لإدخال درجاتك.\n"
        "3. تأكد من إدخال درجات صالحة بين 0 و 20.\n"
        "4. اضغط على <b>/cancel</b> في حالة كنت تريد إيقاف البوت.\n"
        "5. للقيام بإعادة البدء، اضغط أولاً على <b>/cancel</b> ثم <b>/start</b>.\n"
        "إذا كنت بحاجة إلى مساعدة إضافية، تواصل مع @yassineboukerma",
        parse_mode='HTML'
    )

def visitor_count(update: Update, context: CallbackContext) -> None:
    count = get_visitor_count()
    update.message.reply_text(f"The bot has been visited by {count} unique users.")

def overall_average_count(update: Update, context: CallbackContext) -> None:
    count = get_overall_average_count()
    update.message.reply_text(f"The Bot has been used {count} times.")

def show_user_ids(update: Update, context: CallbackContext) -> None:
    user_ids = get_all_user_ids()
    update.message.reply_text(f"Collected user IDs: {', '.join(map(str, user_ids))}")

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Operation cancelled.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def whatsnew(update: Update, context: CallbackContext) -> None:
   update.message.reply_text(MESSAGE_whatsnew, parse_mode='HTML')
   update.message.reply_text(MESSAGE_AR_whatsnew, parse_mode='HTML')

def main() -> None:
    init_db()

    updater = Updater("ur bot token", request_kwargs={'read_timeout': 20, 'connect_timeout': 20})
    dispatcher = updater.dispatcher

    # Notify users that the bot is online
    job_queue = updater.job_queue
    job_queue.run_once(notify_users, 0)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SPECIALIZATION: [MessageHandler(Filters.text & ~Filters.command, choose_specialization)],
            LEVEL: [MessageHandler(Filters.text & ~Filters.command, choose_level)],
            SUB_LEVEL: [MessageHandler(Filters.text & ~Filters.command, choose_sub_level)],
            FIRST: [MessageHandler(Filters.text & ~Filters.command, receive_first_grade)],
            SECOND: [MessageHandler(Filters.text & ~Filters.command, receive_second_grade)],
            TP: [MessageHandler(Filters.text & ~Filters.command, receive_tp_grade)],
            TD: [MessageHandler(Filters.text & ~Filters.command, receive_td_grade)],
            NEXT_SUBJECT: [MessageHandler(Filters.text & ~Filters.command, receive_subject_average)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("visitor_count", visitor_count))
    dispatcher.add_handler(CommandHandler("usage_count", overall_average_count))
    dispatcher.add_handler(CommandHandler("showUserIDs", show_user_ids))
    dispatcher.add_handler(CommandHandler("whats_new", whatsnew))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

