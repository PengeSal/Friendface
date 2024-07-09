from flask import *
from flask_login import *
from bcrypt import *
from secrets import token_hex
from flask_bcrypt import Bcrypt
from datetime import *
import os, base64, random, sqlite3, editdistance
from io import BytesIO
from PIL import Image



app = Flask(__name__, static_url_path='/static')
app.secret_key = token_hex(16)

bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'

class User(UserMixin):
    def __init__(self, user_id, forename, surname, email, password, profile_picture):
        self.id = user_id
        self.forename = forename
        self.surname = surname
        self.email = email
        self.password = password
        self.profile_picture = profile_picture

@app.route('/get_post_id')
@login_required
def get_post_id():
    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    return str(get_max_post_id(cursor) + 1)


def resize(image, targetwidth, formatstate):
    image_data = base64.b64decode(image)
    image = Image.open(BytesIO(image_data))

    originalwidth, originalheight = image.size

    if originalwidth > targetwidth:
        aspectratio = targetwidth / originalwidth
        newwidth = targetwidth
        newheight = int(originalheight * aspectratio)

        resizedimage = image.resize((newwidth, newheight), Image.LANCZOS)
    else:
        resizedimage = image



    transparent = False
    if resizedimage.mode in ('RGBA', 'LA') or (resizedimage.mode == 'P' and 'transparency' in resizedimage.info):
        alpha = resizedimage.convert('RGBA').getchannel('A')
        minalpha = alpha.getextrema()[0]
        if minalpha < 255:
            transparent = True

    if transparent or formatstate=="png":
        formata = 'PNG'
    else:
        formata = 'JPEG'
        resizedimage = resizedimage.convert('RGB')

    resizedio = BytesIO()
    resizedimage.save(resizedio, format=formata)
    resizedio.seek(0)

    resizedimage = base64.b64encode(resizedio.read()).decode('utf-8')

    return resizedimage


@app.route('/get_more_posts')
@login_required
def get_more_posts():
    post_ids = []
    names = []
    messages = []
    user_ids = []
    profile_pictures = []
    likes = []
    dislikes = []
    comments_amounts = []
    photos = []
    times = []
    likers = []
    dislikers = []
    replying_to = []
    replytext = []

    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn2 = sqlite3.connect(db_path)
    cursor2 = conn2.cursor()

    cursor2.execute("""SELECT * FROM posts""")
    posts = cursor2.fetchall()

    columns = {description[0]: index for index, description in enumerate(cursor2.description)}

    random.shuffle(posts)
    selected_posts = posts[:10]

    for post in selected_posts:
        post_id = post[columns['post_id']]
        name = post[columns['name']]
        message = post[columns['message']]
        user_id = post[columns['user_id']]
        like = post[columns['likes']]
        dislike = post[columns['dislikes']]
        photo = post[columns['photo']]
        time = post[columns['time']]
        liker = post[columns['likers']]
        disliker = post[columns['dislikers']]
        reply_to = post[columns['replying_to']]

        post_ids.append(post_id)
        names.append(name)
        messages.append(message)
        user_ids.append(user_id)
        likes.append(like)
        dislikes.append(dislike)
        photos.append(photo)
        times.append(time)
        likers.append(liker)
        dislikers.append(disliker)
        replying_to.append(reply_to)

        try:
            cursor2.execute("""SELECT profile_picture FROM users WHERE user_id=?""", (user_id,))
            pfp = cursor2.fetchone()
            if pfp:
                pfp = pfp[0]
                profile_pictures.append(resize(pfp, 100, "png"))
            else:
                profile_pictures.append("default_picture")
        except Exception as e:
            print(f"Error fetching profile picture for user_id {user_id}: {e}")
            profile_pictures.append("default_picture")


        try:
            cursor2.execute("""SELECT message FROM posts WHERE post_id=?""", (reply_to,))
            replytexta = cursor2.fetchone()
            if replytexta:
                replytext.append(replytexta[0])
            else:
                replytext.append("default_picture")
        except Exception as e:
            print(f"Error fetching profile picture for user_id {post_id}: {e}")
            replytext.append("default_picture")

    print("Post IDs:", post_ids)
    print("User IDs:", user_ids)
    print("Names:", names)

    post_ids_str = "_SEPARATOR_".join(map(str, post_ids))
    names_str = "_SEPARATOR_".join(names)
    messages_str = "_SEPARATOR_".join(messages)
    user_ids_str = "_SEPARATOR_".join(map(str, user_ids))
    profile_pictures_str = "_SEPARATOR_".join(profile_pictures)
    likes_str = "_SEPARATOR_".join(map(str, likes))
    dislikes_str = "_SEPARATOR_".join(map(str, dislikes))
    comments_amounts_str = "_SEPARATOR_".join(map(str, comments_amounts))
    photos_str = "_SEPARATOR_".join(photos)
    times_str = "_SEPARATOR_".join(times)
    likers_str = "_SEPARATOR_".join(likers)
    dislikers_str = "_SEPARATOR_".join(dislikers)
    replying_to_str = "_SEPARATOR_".join(replying_to)
    replytext_str = "_SEPARATOR_".join(replytext)

    posts = f"'{post_ids_str}', '{names_str}', '{messages_str}', '{user_ids_str}', '{profile_pictures_str}', '{likes_str}', '{dislikes_str}', '{comments_amounts_str}', '{photos_str}', '{times_str}', '{likers_str}', '{dislikers_str}', '{replying_to_str}', {current_user.id}, 'no', '{replytext_str}'"

    conn2.close()

    return posts


@login_manager.user_loader
def load_user(user_id):
    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""SELECT * FROM users WHERE user_id=?""", (user_id,))
        user_data = cursor.fetchone()

        if user_data:
            return User(user_data[0], user_data[1], user_data[2], user_data[3], user_data[4], user_data[5])
    except sqlite3.Error:
        pass
    finally:
        conn.close()

    return None

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/loginerror')
def index2():
    return render_template('login2.html')

@app.route('/register', methods=['POST'])
def register():
    return render_template('register.html')

@app.route('/registererror', methods=['POST', "GET"])
def register2():
    return render_template('register2.html')



def get_max_post_id(cursor):
    cursor.execute("SELECT MAX(post_id) FROM posts WHERE deleted = 0")
    result = cursor.fetchone()[0]
    return result if result is not None else 0

@app.route('/createpost/<isreply>/<replying_to>', methods=['POST'])
def create_post(isreply, replying_to):
    data = request.form.get('imageData')

    photo = data.split("_SEPARATINGIMAGEDATAFROMMESSAGEDATA_")[1]
    message = data.split("_SEPARATINGIMAGEDATAFROMMESSAGEDATA_")[0].replace("\n", "_THISISALINEBREAK_").replace("'", "_THISISANAPOSTROPHE_")

    name = f"{current_user.forename} {current_user.surname}"
    user_id = current_user.id
    print(f"USER ID: {user_id}")

    if isreply == "notareply":
        is_reply = "no"
        replying_to = ""
    else:
        is_reply = "yes"
        replying_to = replying_to

    if photo == "":
        is_photo = "no"
    else:
        is_photo = "yes"
        # photo = resize(photo, 1280, "png")

    comments = str([])
    comments_amount = 0
    likes = 0
    dislikes = 0
    views = 0
    likers = ""
    dislikers = ""

    time = datetime.now().strftime("%d/%m/%Y %H:%M")

    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()


    profile_picture = ""

    conn.close()

    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS posts (
            post_id INTEGER PRIMARY KEY,
            name TEXT,
            message TEXT,
            user_id TEXT,
            profile_picture TEXT,
            likes INTEGER,
            dislikes INTEGER,
            comments TEXT,
            comments_amount INTEGER,
            is_reply TEXT,
            is_photo TEXT,
            photo BLOB,
            time TEXT,
            likers TEXT,
            dislikers TEXT,
            replying_to TEXT,
            deleted INTEGER DEFAULT 0,
            views INTEGER)""")

    try:
        max_post_id = get_max_post_id(cursor)
        new_post_id = max_post_id + 1

        cursor.execute("""
                INSERT INTO posts (post_id, name, message, user_id, profile_picture, likes, dislikes, comments, comments_amount, is_reply, is_photo, photo, time, likers, dislikers, replying_to, views)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (new_post_id, name, message, user_id, profile_picture, likes, dislikes, comments, comments_amount, is_reply, is_photo, photo, time, likers, dislikers, replying_to, views))

        conn.commit()

    except sqlite3.IntegrityError:
        return redirect(url_for('home', mode="feed"))
    finally:
        conn.close()

    return redirect(f'/users/{current_user.id}/posts')



@app.route('/like/<likestate>/<int:post_id>', methods=['POST'])
@login_required
def like(likestate, post_id):
    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT likers, likes FROM posts WHERE post_id=?", (post_id,))
    row = cursor.fetchone()
    likers, likes = row[0], row[1]

    likers_list = likers.split("_LIKERS_") if likers else []

    if likestate == "like":
        if str(current_user.id) not in likers_list:
            likers_list.append(str(current_user.id))
            likes += 1
    else:  # unlike
        if str(current_user.id) in likers_list:
            likers_list.remove(str(current_user.id))
            likes -= 1

    likerstring = "_LIKERS_".join(likers_list)

    cursor.execute("UPDATE posts SET likers=?, likes=? WHERE post_id=?", (likerstring, likes, post_id))
    conn.commit()
    conn.close()

    return "biggle"

@app.route('/dislike/<likestate>/<int:post_id>', methods=['POST'])
@login_required
def dislike(likestate, post_id):
    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT dislikers, dislikes FROM posts WHERE post_id=?", (post_id,))
    row = cursor.fetchone()
    dislikers, dislikes = row[0], row[1]

    dislikers_list = dislikers.split("_DISLIKERS_") if dislikers else []

    if likestate == "dislike":
        if str(current_user.id) not in dislikers_list:
            dislikers_list.append(str(current_user.id))
            dislikes += 1
    else:  # undislike
        if str(current_user.id) in dislikers_list:
            dislikers_list.remove(str(current_user.id))
            dislikes -= 1

    dislikerstring = "_DISLIKERS_".join(dislikers_list)

    cursor.execute("UPDATE posts SET dislikers=?, dislikes=? WHERE post_id=?", (dislikerstring, dislikes, post_id))
    conn.commit()
    conn.close()

    return "biggle"




@app.route('/insert', methods=['POST'])
def insert_data():
    forename = request.form['forename']
    surname = request.form['surname']
    email = request.form['email'].lower()
    verify = f"{forename}{surname}{email}"

    password = request.form['password']
    hashed_password = hashpw(password.encode('utf-8'), gensalt())

    image_path = "static/pfp.png"
    with open(image_path, "rb") as file:
        profile_picture = file.read()
    profile_picture = base64.b64encode(profile_picture).decode('utf-8')

    image_path = "static/banner.png"
    with open(image_path, "rb") as file:
        banner = file.read()
    banner = base64.b64encode(banner).decode('utf-8')

    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    followers = 0
    friends = 0

    followinglist = []
    following = str(followinglist)




    friendinglist = []
    friending = str(friendinglist)

    pendingfriendslist = []
    pendingfriends = str(pendingfriendslist)

    about = f"Hello, my name is {forename} and I have yet to make use of the incredible customisation features offered by Friendface©"

    dark_mode = "no"

    try:
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                forename TEXT,
                surname TEXT,
                email TEXT UNIQUE,
                password TEXT,
                verify TEXT,
                profile_picture BLOB,
                banner BLOB,
                friends INTEGER,
                friending TEXT,
                followers INTEGER,
                following TEXT,
                pendingfriends TEXT,
                about TEXT,
                liking TEXT,
                disliking TEXT,
                dark_mode TEXT)""")

        cursor.execute("""
                INSERT INTO users (forename, surname, email, password, verify, profile_picture, banner, friends, friending, followers, following, pendingfriends, about, dark_mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (forename, surname, email.lower(), hashed_password, verify, profile_picture, banner, friends, friending, followers, following, pendingfriends, about, dark_mode))

        conn.commit()

        cursor.execute("""SELECT * FROM users WHERE email=?""", (email.lower(),))
        user_data = cursor.fetchone()

        user = User(user_data[0], user_data[1], user_data[2], user_data[3], user_data[4], user_data[5])
        login_user(user)

    except sqlite3.IntegrityError:
        return redirect(url_for('register2'))
    finally:
        conn.close()

    return redirect(url_for('index'))



@app.route('/changebanner', methods=['GET', 'POST'])
@login_required
def changebanner():
     if request.method == 'POST':
        image_data = request.form.get('imageData')
        image_data = resize(image_data, 1280, "png")

        db_path = os.path.join(os.getcwd(), 'friendface.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""UPDATE users SET banner=? WHERE email=?""", (image_data, current_user.email))
        conn.commit()
        conn.close()

        return "biggle"





@app.route('/darkmode/<yayornay>', methods=["POST"])
@login_required
def darkmode(yayornay):
    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""UPDATE users SET dark_mode=? WHERE email=?""", (yayornay, current_user.email))
    conn.commit()
    conn.close()

    return "biggle"








@app.route('/settings', methods=['GET', "POST"])
@login_required
def settings():
    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""SELECT profile_picture FROM users WHERE email=?""", (current_user.email,))
    user_data = cursor.fetchone()

    cursor.execute("""SELECT user_id FROM users WHERE email=?""", (current_user.email,))
    user_id = cursor.fetchone()
    user_id = user_id[0]

    name = str(f"{current_user.forename} {current_user.surname}")

    image_path = "static/logo.png"
    with open(image_path, "rb") as file:
        logo = file.read()
    logo = base64.b64encode(logo).decode('utf-8')

    with open("splash_messages.txt", "r") as file:
        splashes = file.readlines()
    splash = random.choice(splashes)
    if splash == "Your graphics card has mined 0.056 Bitcoin today!\n":
        splash = f"Your graphics card has mined {random.randint(1, 999)/10000} Bitcoin today!"
    if splash == "Established 2004\n":
        splash = f"Established {random.randint(1997, 2009)}"

    cursor.execute("""SELECT profile_picture FROM users WHERE user_id=?""", (current_user.id,))
    pfp = cursor.fetchone()
    pfp = pfp[0]

    cursor.execute("""SELECT banner FROM users WHERE user_id=?""", (current_user.id,))
    banner = cursor.fetchone()
    banner = banner[0]

    cursor.execute("""SELECT about FROM users WHERE user_id =?""", (user_id,))
    about = cursor.fetchone()
    about = about[0]

    cursor.execute("""SELECT dark_mode FROM users WHERE user_id =?""", (user_id,))
    dark_mode = cursor.fetchone()
    dark_mode = dark_mode[0]

    return render_template('settings.html', profile_picture=user_data[0], theirid = user_id, forename = current_user.forename, surname = current_user.surname, about = about,
                           profile_text=name, logo=logo, user_id = user_id, splashmessage=splash, theirpicture=pfp, theirbanner=banner, dark_mode=dark_mode)





@app.route('/get_random_advert', methods=['GET'])
@login_required
def get_random_advert():
    image_path = f"static/adverts/advert{random.randint(0, 10)}.png"
    with open(image_path, "rb") as file:
        advert = file.read()
    advert = base64.b64encode(advert).decode('utf-8')

    return advert



@app.route('/get/<image>/<post_id>', methods=['GET'])
@login_required
def get_image(image, post_id):
    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if image == "image":
        print(f"POST ID: {post_id}")

        cursor.execute("""SELECT photo FROM posts WHERE post_id=?""", (post_id,))
        photo = cursor.fetchone()
        photo = photo[0]

        return photo

    elif image == "pfp":
        cursor.execute("""SELECT user_id FROM posts WHERE post_id=?""", (post_id,))
        user_id = cursor.fetchone()
        user_id = user_id[0]

        cursor.execute("""SELECT profile_picture FROM users WHERE user_id=?""", (user_id,))
        pfp = cursor.fetchone()
        pfp = pfp[0]

        return resize(pfp, 100, "png")

    elif image == "pfp_comment":
        cursor.execute("""SELECT profile_picture FROM users WHERE user_id=?""", (post_id,))
        pfp = cursor.fetchone()
        pfp = pfp[0]

        return resize(pfp, 100, "png")

    elif image == "reply_message":
        cursor.execute("""SELECT message FROM posts WHERE post_id=?""", (post_id,))
        message = cursor.fetchone()
        message = message[0]

        return message

    elif image == "album":
        cursor.execute("""SELECT * FROM posts WHERE user_id = ?""", (post_id,))
        posts = cursor.fetchall()

        photoalbum = ""
        increment = 0


        for post in reversed(posts):
            for column_name, value in zip(cursor.description, post):
                if column_name[0] == "photo":
                    if value != "":
                        print("PHOTOYES")
                        increment += 1
                        photoalbum = f"{photoalbum}{resize(value, 1280, 'png')}_SEPARATOR_"
                    if increment >= 9:
                        return photoalbum

        return photoalbum







@app.route('/edit_post/<what>/<int:post_id>', methods=['POST'])
@login_required
def edit_post(what, post_id):
    if what == "message":
        image_data = request.form.get('imageData').replace("\n", "_THISISALINEBREAK_").replace("'", "_THISISANAPOSTROPHE_")



        db_path = os.path.join(os.getcwd(), 'friendface.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()


        print("LMAO BLUD: " + image_data)
        cursor.execute("""UPDATE posts SET message=? WHERE post_id=?""", (image_data, post_id))


        conn.commit()
        conn.close()

        return "biggle"

    else:
        image_data = request.form.get('imageData')

        print(image_data)

        db_path = os.path.join(os.getcwd(), 'friendface.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()


        cursor.execute("""UPDATE posts SET photo=? WHERE post_id=?""", (image_data, post_id))


        conn.commit()
        conn.close()

        return "biggle"




@app.route('/deletecomment/<comment_id>/<post_id>', methods=['GET', 'POST'])
@login_required
def deletecomment(comment_id, post_id):
     if request.method == 'POST':
        db_path = os.path.join(os.getcwd(), 'friendface.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()


        cursor.execute("""SELECT comments FROM posts WHERE post_id=?""", (post_id,))
        user_data7 = cursor.fetchone()
        followinglist = eval(user_data7[0])

        for item in followinglist:
            items = item.split("_COMMENTS_")

            commentid2 = items[4]

            if commentid2 == comment_id:
                followinglist.remove(item)


        following = str(followinglist)
        cursor.execute("""UPDATE posts SET comments=? WHERE post_id=?""", (following, post_id,))

        conn.commit()
        conn.close()







        return "biggle"





@app.route('/addcomment/<post_id>', methods=['GET', 'POST'])
@login_required
def addcomment(post_id):
    comment = request.form.get('imageData')

    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()


    cursor.execute("""SELECT comments FROM posts WHERE post_id=?""", (post_id,))
    user_data = cursor.fetchone()
    followinglist = eval(user_data[0])

    conn.close()
    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()



    name = f"{current_user.forename} {current_user.surname}"

    conn.close()
    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    comment = comment.replace("'", "_THISISANAPOSTROPHE_")


    commentid = random.randint(10000000000000000, 99999999999999999)

    followinglist.append(f"{comment}_COMMENTS_{name}_COMMENTS_profile_picture_COMMENTS_{current_user.id}_COMMENTS_{commentid}")
    following = str(followinglist)

    print("COMMENTID: " + str(commentid))

    cursor.execute("""UPDATE posts SET comments=? WHERE post_id=?""", (following, post_id,))




    conn.commit()
    conn.close()
    return redirect(f"/posts/{post_id}")






def lenient_search_forenames(cursor, searchterm, similarity_threshold=0.6):
    matching_names_and_ids = ""

    cursor.execute("""SELECT forename, user_id FROM users""")
    all_names_and_ids = cursor.fetchall()

    searchterm = searchterm.lower().strip()

    matching_names_and_ids = []
    for result in all_names_and_ids:
        try:
            forename = result[0].lower().strip()
            user_id = result[1]
            distance = editdistance.eval(searchterm, forename)
            similarity = 1 - (distance / max(len(searchterm), len(forename)))
            if similarity >= similarity_threshold:
                matching_names_and_ids.append({"forename": forename, "user_id": user_id})
        except:
            pass


    return matching_names_and_ids

def lenient_search_surnames(cursor, searchterm, similarity_threshold=0.6):
    matching_surnames_and_ids = ""

    cursor.execute("""SELECT surname, user_id FROM users""")
    all_surnames_and_ids = cursor.fetchall()

    searchterm = searchterm.lower().strip()

    matching_surnames_and_ids = []
    for result in all_surnames_and_ids:
        try:
            surname = result[0].lower().strip()
            user_id = result[1]
            distance = editdistance.eval(searchterm, surname)
            similarity = 1 - (distance / max(len(searchterm), len(surname)))
            if similarity >= similarity_threshold:
                matching_surnames_and_ids.append({"surname": surname, "user_id": user_id})
        except:
            pass
    
    return matching_surnames_and_ids

@app.route('/searchusers', methods=['GET'])
@login_required
def search_users():
    searchterm = request.args.get('search')

    searchterm2 = searchterm.split(" ")
    forename = searchterm2[0]

    try:
        surname = searchterm2[1]
    except:
        surname = ""

    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""SELECT profile_picture FROM users WHERE email=?""", (current_user.email,))
    user_data = cursor.fetchone()

    cursor.execute("""SELECT user_id FROM users WHERE email=?""", (current_user.email,))
    user_id = cursor.fetchone()
    user_id = user_id[0]

    name = str(f"{current_user.forename} {current_user.surname}")

    image_path = "static/logo.png"
    with open(image_path, "rb") as file:
        logo = file.read()
    logo = base64.b64encode(logo).decode('utf-8')

    with open("splash_messages.txt", "r") as file:
        splashes = file.readlines()
    splash = random.choice(splashes)
    if splash == "Your graphics card has mined 0.056 Bitcoin today!\n":
        splash = f"Your graphics card has mined {random.randint(1, 999)/10000} Bitcoin today!"
    if splash == "Established 2004\n":
        splash = f"Established {random.randint(1997, 2009)}"


    matching_forenames = lenient_search_forenames(cursor, forename)
    matching_surnames = lenient_search_surnames(cursor, surname)

    matching_forenames2 = lenient_search_forenames(cursor, surname)
    matching_surnames2 = lenient_search_surnames(cursor, forename)

    matches = []

    for match in matching_forenames:
        print(f"Forename: {match['forename']}, User ID: {match['user_id']}")
        matches.append(match['user_id'])

    for match in matching_surnames:
        print(f"Surname: {match['surname']}, User ID: {match['user_id']}")
        matches.append(match['user_id'])

    for match in matching_forenames2:
        print(f"Forename: {match['forename']}, User ID: {match['user_id']}")
        matches.append(match['user_id'])

    for match in matching_surnames2:
        print(f"Surname: {match['surname']}, User ID: {match['user_id']}")
        matches.append(match['user_id'])

    print(matches)
    matches = list(dict.fromkeys(matches))


    user_ids = ""
    names = ""
    pfps = ""
    descriptions = ""

    for item in matches:
        cursor.execute("""SELECT profile_picture FROM users WHERE user_id=?""", (item,))
        pfp = cursor.fetchone()
        pfp = pfp[0]

        cursor.execute("""SELECT forename FROM users WHERE user_id=?""", (item,))
        forename = cursor.fetchone()
        forename = forename[0]

        cursor.execute("""SELECT surname FROM users WHERE user_id=?""", (item,))
        surname = cursor.fetchone()
        surname = surname[0]

        cursor.execute("""SELECT about FROM users WHERE user_id=?""", (item,))
        description = cursor.fetchone()
        description = description[0]

        names = f"{names}{forename} {surname}_MATCHES_"
        pfps = f"{pfps}{pfp}_MATCHES_"
        user_ids = f"{user_ids}{item}_MATCHES_"
        descriptions = f"{descriptions}{description}_MATCHES_"


    displaymatches = f"displaymatches('{names}', '{pfps}', '{user_ids}', '{descriptions}')"

    searchterm = f'Showing results for "{searchterm}"'




    return render_template('search_users.html', profile_picture=user_data[0], profile_text=name, logo=logo, user_id = user_id, splashmessage=splash, searchterm = searchterm, displaymatches = displaymatches)







@app.route('/posts/<int:post_id>', methods=['GET', 'POST'])
@login_required
def posts(post_id):
    try:
        db_path = os.path.join(os.getcwd(), 'friendface.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        user_id = current_user.id

        cursor.execute("""SELECT * FROM users WHERE user_id=?""", (user_id,))
        user_data = cursor.fetchone()

        if user_data:
            db_path = os.path.join(os.getcwd(), 'friendface.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""SELECT profile_picture FROM users WHERE email=?""", (current_user.email,))
            user_data = cursor.fetchone()

            name3 = str(f"{current_user.forename} {current_user.surname}")

            cursor.execute("""SELECT user_id FROM users WHERE email=?""", (current_user.email,))
            user_id1 = cursor.fetchone()
            user_id1 = user_id1[0]

            image_path = "static/logo.png"
            with open(image_path, "rb") as file:
                logo = file.read()
            logo = base64.b64encode(logo).decode('utf-8')

            with open("splash_messages.txt", "r") as file:
                splashes = file.readlines()
            splash = random.choice(splashes)
            if splash == "Your graphics card has mined 0.056 Bitcoin today!\n":
                splash = f"Your graphics card has mined {random.randint(1, 999)/10000} Bitcoin today!"
            if splash == "Established 2004\n":
                splash = f"Established {random.randint(1997, 2009)}"

            conn.close()






            db_path = os.path.join(os.getcwd(), 'friendface.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""SELECT photo FROM posts WHERE post_id=?""", (post_id,))
            profile_picture2 = cursor.fetchone()
            image = profile_picture2[0]

            cursor.execute("""SELECT name FROM posts WHERE post_id=?""", (post_id,))
            name = cursor.fetchone()
            name = name[0]

            cursor.execute("""SELECT time FROM posts WHERE post_id=?""", (post_id,))
            date = cursor.fetchone()
            date = date[0]

            cursor.execute("""SELECT user_id FROM posts WHERE post_id=?""", (post_id,))
            theirid = cursor.fetchone()
            theirid = theirid[0]

            cursor.execute("""SELECT profile_picture FROM users WHERE user_id=?""", (theirid,))
            pfp = cursor.fetchone()
            pfp = pfp[0]

            cursor.execute("""SELECT message FROM posts WHERE post_id=?""", (post_id,))
            message = cursor.fetchone()
            message = message[0]



            cursor.execute("""SELECT likers FROM posts WHERE post_id=?""", (post_id,))
            likers2 = cursor.fetchone()
            likers2 = likers2[0]

            cursor.execute("""SELECT dislikers FROM posts WHERE post_id=?""", (post_id,))
            dislikers2 = cursor.fetchone()
            dislikers2 = dislikers2[0]

            cursor.execute("""SELECT likes FROM posts WHERE post_id=?""", (post_id,))
            likes2 = cursor.fetchone()
            likes2 = likes2[0]

            cursor.execute("""SELECT dislikes FROM posts WHERE post_id=?""", (post_id,))
            dislikes2 = cursor.fetchone()
            dislikes2 = dislikes2[0]

            cursor.execute("""SELECT is_photo FROM posts WHERE post_id=?""", (post_id,))
            isphoto = cursor.fetchone()
            isphoto = isphoto[0]

            cursor.execute("""SELECT is_reply FROM posts WHERE post_id=?""", (post_id,))
            isreply = cursor.fetchone()
            isreply = isreply[0]

            cursor.execute("""SELECT replying_to FROM posts WHERE post_id=?""", (post_id,))
            replying_to2 = cursor.fetchone()
            replying_to2 = replying_to2[0]


            cursor.execute("""SELECT views FROM posts WHERE post_id=?""", (post_id,))
            views = cursor.fetchone()
            views = views[0]





            messages2 = ""
            user_ids2 = ""
            names2 = ""
            pfps2 = ""
            commentids2 = ""

            cursor.execute("""SELECT comments FROM posts WHERE post_id=?""", (post_id,))
            user_data7 = cursor.fetchone()
            user_data7 = eval(user_data7[0])

            conn.commit()
            conn.close()

            db_path = os.path.join(os.getcwd(), 'friendface.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()


            for item in user_data7:
                items = item.split("_COMMENTS_")



                message2 = items[0]
                user_id2 = items[3]

                cursor.execute("""SELECT forename FROM users WHERE user_id=?""", (user_id2,))
                forename2 = cursor.fetchone()
                forename2 = forename2[0]

                cursor.execute("""SELECT surname FROM users WHERE user_id=?""", (user_id2,))
                surname2 = cursor.fetchone()
                surname2 = surname2[0]

                name2 = f"{forename2} {surname2}"




                commentid2 = items[4]




                messages2 = f"{messages2}{message2}_COMMENTS_"
                pfps2 = f"{pfps2}image_COMMENTS_"
                names2 = f"{names2}{name2}_COMMENTS_"
                user_ids2 = f"{user_ids2}{user_id2}_COMMENTS_"
                commentids2 = f"{commentids2}{commentid2}_COMMENTS_"


            commentslist = f"displaycomments('{messages2}', '{names2}', '{pfps2}', '{user_ids2}', '{commentids2}', '{current_user.id}', '{post_id}')"

            post_ids = ""
            names = ""
            messages = ""
            user_ids = ""
            profile_pictures = ""
            likes = ""
            dislikes = ""
            comments_amounts = ""
            photos = ""
            times = ""
            likers = ""
            dislikers = ""
            replying_to = ""

            db_path = os.path.join(os.getcwd(), 'friendface.db')
            conn2 = sqlite3.connect(db_path)
            cursor2 = conn2.cursor()


            cursor2.execute("""SELECT * FROM posts WHERE replying_to = ?""", (post_id,))
            posts = cursor2.fetchall()



            for post in posts:
                for column_name, value in zip(cursor2.description, post):


                    if column_name[0] == "post_id":
                        post_ids = f"{post_ids}{value}_SEPARATOR_"
                    if column_name[0] == "name":
                        names = f"{names}{value}_SEPARATOR_"
                    if column_name[0] == "message":
                        messages = f"{messages}{value}_SEPARATOR_"
                    if column_name[0] == "user_id":
                        user_ids = f"{user_ids}{value}_SEPARATOR_"
                    if column_name[0] == "profile_picture":
                        profile_pictures = f"{profile_pictures}image_SEPARATOR_"
                    if column_name[0] == "likes":
                        likes = f"{likes}{value}_SEPARATOR_"
                    if column_name[0] == "dislikes":
                        dislikes = f"{dislikes}{value}_SEPARATOR_"
                    if column_name[0] == "comments_amounts":
                        comments_amounts = f"{comments_amounts}{value}_SEPARATOR_"
                    if column_name[0] == "is_photo":
                        if value != "no":
                            print("THIS IS A PHOTO")
                            print("THIS IS A PHOTO")
                            print("THIS IS A PHOTO")

                            photos = f"{photos}image_SEPARATOR_"
                        else:
                            photos = f"{photos}_SEPARATOR_"
                            print("THIS IS NOT NOT NOT A PHOTO")
                            print("THIS IS NOT NOT NOT A PHOTO")
                            print("THIS IS NOT NOT NOT A PHOTO")


                    if column_name[0] == "time":
                        times = f"{times}{value}_SEPARATOR_"
                    if column_name[0] == "likers":
                        likers = f"{likers}{value}_SEPARATOR_"
                    if column_name[0] == "dislikers":
                        dislikers = f"{dislikers}{value}_SEPARATOR_"
                    if column_name[0] == "replying_to":
                        replying_to = f"{replying_to}{value}_SEPARATOR_"


            posts = f"displayposts('{post_ids}', '{names}', '{messages}', '{user_ids}', '{profile_pictures}', '{likes}', '{dislikes}', '{comments_amounts}', '{photos}', '{times}', '{likers}', '{dislikers}', '{replying_to}', {current_user.id})"








            userdata = user_data[0]

            newposts = f"newpost('{current_user.forename} {current_user.surname}', '{userdata}', '{current_user.id}', '{post_id}')"

            cursor.execute("""SELECT * FROM users WHERE user_id=?""", (theirid,))
            user_data2 = cursor.fetchone()

            if user_data:
                banner = user_data2[7]
                conn.close()


            if isphoto == "yes":
                return render_template("posts_image.html", theirname=name, views=views,
                    theirpicture=pfp, profile_picture=userdata, pfp=pfp, theirid = theirid, likebutton = f"likebutton('{likers2}', '{current_user.id}', '{post_id}', '{likes2}')",
                    profile_text=name3, logo=logo, date=date, message=message, dislikebutton = f"dislikebutton('{dislikers2}', '{current_user.id}', '{post_id}', '{dislikes2}')",
                    likes=likes2, dislikes=dislikes2, newposts = newposts, theirbanner = banner,
                    user_id = user_id1, splashmessage = splash, image=image, post_id=post_id, commentslist=commentslist, isreply = isreply, replying_to=replying_to2, displayposts = posts)

            else:
                return render_template("posts_message.html", theirname=name, views=views,
                    theirpicture=pfp, profile_picture=userdata, pfp=pfp, theirid = theirid, likebutton = f"likebutton('{likers2}', '{current_user.id}', '{post_id}', '{likes2}')",
                    profile_text=name3, logo=logo, date=date, message=message, dislikebutton = f"dislikebutton('{dislikers2}', '{current_user.id}', '{post_id}', '{dislikes2}')",
                    likes=likes2, dislikes=dislikes2, newposts = newposts, theirbanner = banner,
                    user_id = user_id1, splashmessage = splash, image=image, post_id=post_id, commentslist=commentslist, isreply = isreply, replying_to=replying_to2, displayposts = posts)

    except TypeError as e:
        encoded_error = base64.b64encode(str(e).encode()).decode()
        return redirect(f"/post_not_found/{encoded_error}")




@app.route('/post_not_found/<error>', methods=['GET'])
@login_required
def post_not_found(error):
    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""SELECT profile_picture FROM users WHERE email=?""", (current_user.email,))
    user_data = cursor.fetchone()

    cursor.execute("""SELECT user_id FROM users WHERE email=?""", (current_user.email,))
    user_id = cursor.fetchone()
    user_id = user_id[0]

    name = str(f"{current_user.forename} {current_user.surname}")

    image_path = "static/logo.png"
    with open(image_path, "rb") as file:
        logo = file.read()
    logo = base64.b64encode(logo).decode('utf-8')

    image_path = "static/dead_body.png"
    with open(image_path, "rb") as file:
        dead_body = file.read()
    dead_body = base64.b64encode(dead_body).decode('utf-8')

    with open("splash_messages.txt", "r") as file:
        splashes = file.readlines()
    splash = random.choice(splashes)
    if splash == "Your graphics card has mined 0.056 Bitcoin today!\n":
        splash = f"Your graphics card has mined {random.randint(1, 999)/10000} Bitcoin today!"
    if splash == "Established 2004\n":
        splash = f"Established {random.randint(1997, 2009)}"


    return render_template('post_not_found.html', profile_picture=user_data[0], profile_text=name,
                           logo=logo, user_id = user_id, splashmessage=splash, dead_body=dead_body, error=error)









@app.route('/addfollower/<int:user_id>', methods=['POST', 'GET'])
@login_required
def addfollower(user_id):
    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""SELECT following FROM users WHERE email=?""", (current_user.email,))
    user_data = cursor.fetchone()
    followinglist = eval(user_data[0])
    if user_id in followinglist:
        return "biggle"
    else:
        followinglist.append(user_id)
        following = str(followinglist)
        cursor.execute("""UPDATE users SET following=? WHERE email=?""", (following, current_user.email,))

    cursor.execute("""UPDATE users SET followers=followers+1 WHERE user_id=?""", (user_id,))
    conn.commit()
    conn.close()
    return "biggle"

@app.route('/removefollower/<int:user_id>', methods=['POST', 'GET'])
@login_required
def removefollower(user_id):
    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""SELECT following FROM users WHERE email=?""", (current_user.email,))
    user_data = cursor.fetchone()
    followinglist = eval(user_data[0])
    if user_id in followinglist:
        followinglist.remove(user_id)
        following = str(followinglist)
        cursor.execute("""UPDATE users SET following=? WHERE email=?""", (following, current_user.email,))
    else:
        return "biggle"
    cursor.execute("""UPDATE users SET followers=followers-1 WHERE user_id=?""", (user_id,))
    conn.commit()
    conn.close()
    return "biggle"




@app.route('/delete/<int:post_id>', methods=['POST', 'GET'])
@login_required
def deletepost(post_id):
    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""SELECT user_id FROM posts WHERE post_id=?""", (post_id,))
    user_id = cursor.fetchone()
    user_id = user_id[0]


    if str(user_id) == str(current_user.id):
        cursor.execute("""DELETE FROM posts WHERE post_id=?""", (post_id,))

    conn.commit()
    conn.close()

    return "biggle"








def get_db_connection():
    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/declinefriend/<int:user_id>', methods=['POST'])
@login_required
def declinefriend(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pendingfriends FROM users WHERE email=?", (current_user.email,))
    user_data = cursor.fetchone()
    if user_data:
        pending_friends = json.loads(user_data['pendingfriends'])
        if user_id in pending_friends:
            pending_friends.remove(user_id)
            cursor.execute("UPDATE users SET pendingfriends=? WHERE email=?", 
                           (json.dumps(pending_friends), current_user.email))
            conn.commit()
        else:
            return "Friend request not found", 400
    conn.close()
    return redirect(url_for("home"))

@app.route('/sendfriendrequest/<int:user_id>', methods=['POST', 'GET'])
@login_required
def sendfriendrequest(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pendingfriends FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        pending_friends = json.loads(user_data['pendingfriends'])
        cursor.execute("SELECT user_id FROM users WHERE email=?", (current_user.email,))
        current_user_id = cursor.fetchone()['user_id']
        if current_user_id not in pending_friends:
            pending_friends.append(current_user_id)
            cursor.execute("UPDATE users SET pendingfriends=? WHERE user_id=?", 
                           (json.dumps(pending_friends), user_id))
            conn.commit()
        else:
            return "Friend request already sent", 400
    conn.close()
    return "Friend request sent"

@app.route('/unfriend/<int:user_id>', methods=['POST', 'GET'])
@login_required
def unfriend(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT friending FROM users WHERE email=?", (current_user.email,))
        user_data = cursor.fetchone()
        
        if user_data:
            friending = json.loads(user_data['friending'])

            cursor.execute("SELECT friending FROM users WHERE user_id=?", (user_id,))
            friend_data = cursor.fetchone()
            
            if friend_data:
                friend_friending = json.loads(friend_data['friending'])
                
                cursor.execute("SELECT user_id FROM users WHERE email=?", (current_user.email,))
                current_user_id = cursor.fetchone()['user_id']
                
                if user_id in friending:
                    friending.remove(user_id)
                    if current_user_id in friend_friending:
                        friend_friending.remove(current_user_id)
                    
                    cursor.execute("UPDATE users SET friending=? WHERE email=?", 
                                   (json.dumps(friending), current_user.email))
                    cursor.execute("UPDATE users SET friending=? WHERE user_id=?", 
                                   (json.dumps(friend_friending), user_id))
                    
                    cursor.execute("UPDATE users SET friends=friends-1 WHERE email=?", 
                                   (current_user.email,))
                    cursor.execute("UPDATE users SET friends=friends-1 WHERE user_id=?", 
                                   (user_id,))
                    
                    conn.commit()
                else:
                    return "User not in friend list", 400
            else:
                return "Friend data not found", 400
        else:
            return "User data not found", 400
    except Exception as e:
        conn.rollback()
        print(f"An error occurred: {e}")
        return "An error occurred while processing the request", 500
    finally:
        conn.close()
    
    return "Unfriended successfully"


@app.route('/acceptfriend/<int:user_id>', methods=['POST'])
@login_required
def acceptfriend(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT friending, pendingfriends FROM users WHERE email=?", (current_user.email,))
        user_data = cursor.fetchone()
        
        if user_data:
            friending = json.loads(user_data['friending'])
            pending_friends = json.loads(user_data['pendingfriends'])
            
            cursor.execute("SELECT friending FROM users WHERE user_id=?", (user_id,))
            friend_data = cursor.fetchone()
            
            if friend_data:
                friend_friending = json.loads(friend_data['friending'])
                
                if user_id in pending_friends:
                    friending.append(user_id)
                    friend_friending.append(current_user.id)
                    pending_friends.remove(user_id)

                    print("friending: " + str(friending))
                    print("friend_friending: " + str(friend_friending))
                    print("pending_friends: " + str(pending_friends))
                    
                    cursor.execute(
                        "UPDATE users SET friending=?, pendingfriends=? WHERE email=?", 
                        (json.dumps(friending), json.dumps(pending_friends), current_user.email)
                    )
                    cursor.execute(
                        "UPDATE users SET friending=? WHERE user_id=?", 
                        (json.dumps(friend_friending), user_id))
                    
                    cursor.execute("UPDATE users SET friends = friends + 1 WHERE email=?", (current_user.email,))
                    cursor.execute("UPDATE users SET friends = friends + 1 WHERE user_id=?", (user_id,))
                    
                    conn.commit()
                else:
                    return "Friend request not found", 400
        else:
            return "User data not found", 400
    except Exception as e:
        conn.rollback()
        print(f"An error occurred: {e}")
        return "An error occurred while processing the request", 500
    finally:
        conn.close()
        
    return "Friend request accepted"

@app.route('/alreadypending', methods=['POST', 'GET'])
@login_required
def alreadypending():
    return "Friend request already pending"











@app.route('/home/<mode>', methods=['GET', 'POST'])
@login_required
def home(mode):
    if request.method == 'POST':
        image_data = request.form.get('imageData')

        db_path = os.path.join(os.getcwd(), 'friendface.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        image_data = resize(image_data, 500, "png")

        cursor.execute("""UPDATE users SET profile_picture=? WHERE email=?""", (image_data, current_user.email))



        conn.commit()
        conn.close()

        try:
            db_path = os.path.join(os.getcwd(), 'friendface.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""UPDATE posts SET profile_picture=? WHERE user_id=?""", (image_data, current_user.id))



            conn.commit()
            conn.close()
        except:
            pass

        return "biggle"




    else:
        db_path = os.path.join(os.getcwd(), 'friendface.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""SELECT profile_picture FROM users WHERE email=?""", (current_user.email,))
        user_data = cursor.fetchone()

        cursor.execute("""SELECT user_id FROM users WHERE email=?""", (current_user.email,))
        user_id = cursor.fetchone()
        user_id = user_id[0]

        name = str(f"{current_user.forename} {current_user.surname}")



        image_path = "static/logo.png"
        with open(image_path, "rb") as file:
            logo = file.read()
        logo = base64.b64encode(logo).decode('utf-8')



        with open("splash_messages.txt", "r") as file:
            splashes = file.readlines()
        splash = random.choice(splashes)
        if splash == "Your graphics card has mined 0.056 Bitcoin today!\n":
            splash = f"Your graphics card has mined {random.randint(1, 999)/10000} Bitcoin today!"
        if splash == "Established 2004\n":
            splash = f"Established {random.randint(1997, 2009)}"


        if user_data:
            user_data = user_data[0]
            conn.close()



            post_ids = ""
            names = ""
            messages = ""
            user_ids = ""
            profile_pictures = ""
            likes = ""
            dislikes = ""
            comments_amounts = ""
            photos = ""
            times = ""
            likers = ""
            dislikers = ""
            replying_to = ""

            db_path = os.path.join(os.getcwd(), 'friendface.db')
            conn2 = sqlite3.connect(db_path)
            cursor2 = conn2.cursor()

            try:
                cursor2.execute("""SELECT * FROM posts""")
                posts = cursor2.fetchall()
            except:
                posts = ""

            random.shuffle(posts)
            selected_posts = posts[:10]

            for post in selected_posts:
                for column_name, value in zip(cursor2.description, post):
                    if column_name[0] == "post_id":
                        post_ids = f"{post_ids}{value}_SEPARATOR_"
                    if column_name[0] == "name":
                        names = f"{names}{value}_SEPARATOR_"
                    if column_name[0] == "message":
                        messages = f"{messages}{value}_SEPARATOR_"
                    if column_name[0] == "user_id":
                        user_ids = f"{user_ids}{value}_SEPARATOR_"
                    if column_name[0] == "profile_picture":
                        profile_pictures = f"{profile_pictures}image_SEPARATOR_"
                    if column_name[0] == "likes":
                        likes = f"{likes}{value}_SEPARATOR_"
                    if column_name[0] == "dislikes":
                        dislikes = f"{dislikes}{value}_SEPARATOR_"
                    if column_name[0] == "comments_amounts":
                        comments_amounts = f"{comments_amounts}{value}_SEPARATOR_"
                    if column_name[0] == "is_photo":
                        if value != "no":
                            print("THIS IS A PHOTO")
                            print("THIS IS A PHOTO")
                            print("THIS IS A PHOTO")

                            photos = f"{photos}image_SEPARATOR_"
                        else:
                            photos = f"{photos}_SEPARATOR_"
                            print("THIS IS NOT NOT NOT A PHOTO")
                            print("THIS IS NOT NOT NOT A PHOTO")
                            print("THIS IS NOT NOT NOT A PHOTO")


                    if column_name[0] == "time":
                        times = f"{times}{value}_SEPARATOR_"
                    if column_name[0] == "likers":
                        likers = f"{likers}{value}_SEPARATOR_"
                    if column_name[0] == "dislikers":
                        dislikers = f"{dislikers}{value}_SEPARATOR_"
                    if column_name[0] == "replying_to":
                        replying_to = f"{replying_to}{value}_SEPARATOR_"

            posts = f"displayposts('{post_ids}', '{names}', '{messages}', '{user_ids}', '{profile_pictures}', '{likes}', '{dislikes}', '{comments_amounts}', '{photos}', '{times}', '{likers}', '{dislikers}', '{replying_to}', {current_user.id}, 'yes', '')"

            conn2.close()

            if mode == "feed":
                return render_template('index.html', profile_picture=user_data, profile_text=name,
                                       logo=logo, user_id = user_id, splashmessage=splash, displayposts = posts, forename = current_user.forename)

            elif mode == "liked":
                return render_template('index.html', profile_picture=user_data, profile_text=name,
                                       logo=logo, user_id = user_id, splashmessage=splash, displayposts = posts, forename = current_user.forename)

            elif mode == "most_viewed":
                return render_template('index.html', profile_picture=user_data, profile_text=name,
                                       logo=logo, user_id = user_id, splashmessage=splash, displayposts = posts, forename = current_user.forename)


        else:
            conn.close()
            return render_template('index.html', profile_picture=None)




def changedescription_func(description, location):
    description2 = []

    description2.append(description)



    description2 = description2[0].replace("\r\n", "_THISISALINEBREAK_").replace("'", "_THISISANAPOSTROPHE_")

    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""UPDATE users SET about=? WHERE email=?""", (description2, current_user.email))
    conn.commit()
    conn.close()

    if location == "fromsettings":
        return "/settings"
    else:
        return f"/users/{current_user.id}/about"



@app.route('/changedescription', methods=["POST"])
@login_required
def changedescription():
    description = request.form['desc']
    return redirect(changedescription_func(description, "nope"))


@app.route('/changedescription_fromsettings', methods=["POST"])
@login_required
def changedescription_fromsettings():
    description = request.form['desc']
    return redirect(changedescription_func(description, "fromsettings"))

















@app.route('/about', methods=["POST"])
@login_required
def about():
    return redirect(f"/users/{current_user.id}/about")



def changenames_func(forename, surname, location):
    listy = [forename, surname]

    forename = listy[0].replace("\r\n","")
    surname = listy[1].replace("\r\n", "")


    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""UPDATE users SET forename=? WHERE email=?""", (forename, current_user.email))
    cursor.execute("""UPDATE users SET surname=? WHERE email=?""", (surname, current_user.email))
    conn.commit()
    conn.close()


    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""UPDATE posts SET name=? WHERE user_id=?""", (f"{forename} {surname}", current_user.id))

    conn.commit()
    conn.close()

    if location == "fromsettings":
        return "/settings"
    else:
        return f"/users/{current_user.id}/about"



@app.route('/changenames', methods=["POST"])
@login_required
def changenames():
    forename = request.form['forename']
    surname = request.form['surname']
    return redirect(changenames_func(forename, surname, "nope"))


@app.route('/changenames_fromsettings', methods=["POST"])
@login_required
def changenames_fromsettings():
    forename = request.form['forename']
    surname = request.form['surname']
    return redirect(changenames_func(forename, surname, "fromsettings"))





@app.route('/users/<int:user_id>/<typeofthing>')
@login_required
def user_profile(user_id, typeofthing):
    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""SELECT * FROM users WHERE user_id=?""", (user_id,))
        user_data = cursor.fetchone()

        if user_data:
            name = str(f"{user_data[1]} {user_data[2]}")
            profile_picture = user_data[6]
            banner = user_data[7]
            conn.close()



            db_path = os.path.join(os.getcwd(), 'friendface.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""SELECT profile_picture FROM users WHERE email=?""", (current_user.email,))
            user_data = cursor.fetchone()

            name2 = str(f"{current_user.forename} {current_user.surname}")

            cursor.execute("""SELECT user_id FROM users WHERE email=?""", (current_user.email,))
            user_id1 = cursor.fetchone()
            user_id1 = user_id1[0]

            image_path = "static/logo.png"
            with open(image_path, "rb") as file:
                logo = file.read()
            logo = base64.b64encode(logo).decode('utf-8')

            with open("splash_messages.txt", "r") as file:
                splashes = file.readlines()
            splash = random.choice(splashes)
            if splash == "Your graphics card has mined 0.056 Bitcoin today!\n":
                splash = f"Your graphics card has mined {random.randint(1, 999)/10000} Bitcoin today!"
            if splash == "Established 2004\n":
                splash = f"Established {random.randint(1997, 2009)}"




            cursor.execute("""SELECT followers FROM users WHERE user_id=?""", (user_id,))
            user_data2 = cursor.fetchone()

            print(user_data2[0])

            followers = user_data2[0]

            cursor.execute("""SELECT following FROM users WHERE email =?""", (current_user.email,))
            user_data2 = cursor.fetchone()
            user_data2 = eval(user_data2[0])

            if user_id in user_data2:
                onclick = "follow('unfollow')"
                followbuttonmessage = "Become Judas"
                followbuttonstate = "changebuttoncolor('unfollow')"
            else:
                onclick = "follow('follow')"
                followbuttonstate = "changebuttoncolor('follow')"
                followbuttonmessage = "Become a Disciple"




            cursor.execute("""SELECT friends FROM users WHERE user_id=?""", (user_id,))
            user_data3 = cursor.fetchone()

            print(user_data3[0])

            friends = user_data3[0]

            cursor.execute("""SELECT friending FROM users WHERE user_id =?""", (user_id,))
            user_data3 = cursor.fetchone()
            user_data3 = eval(user_data3[0])

            cursor.execute("""SELECT friending FROM users WHERE email =?""", (current_user.email,))
            user_data5 = cursor.fetchone()
            user_data5 = eval(user_data5[0])

            cursor.execute("""SELECT pendingfriends FROM users WHERE user_id =?""", (user_id,))
            user_data4 = cursor.fetchone()
            user_data4 = eval(user_data4[0])

            if user_id in user_data5:
                onclickfriend = "friend('unfriend')"
                friendbuttonmessage = "Unfriend"
            elif user_id1 in user_data4:
                onclickfriend = "friend('alreadypending')"
                friendbuttonmessage = "Sent"
            else:
                onclickfriend = "friend('friend')"
                friendbuttonmessage = "Friend"



            userdata = user_data[0]
            user_ids = ""
            forenames = ""
            surnames = ""
            pendingfriendlist = ""
            friendlist = ""
            pfps = ""
            descriptions = ""

            for item in user_data4:
                user_ids = f"{user_ids}{item}_SEPARATOR_"

                cursor.execute("""SELECT forename FROM users WHERE user_id =?""", (item,))
                forename = cursor.fetchone()
                try:
                    forename = forename[0]
                except:
                    continue

                forenames = f"{forenames}{forename}_SEPARATOR_"


                cursor.execute("""SELECT surname FROM users WHERE user_id =?""", (item,))
                surname = cursor.fetchone()
                surname = surname[0]

                cursor.execute("""SELECT profile_picture FROM users WHERE user_id =?""", (item,))
                pfp = cursor.fetchone()
                pfp = pfp[0]

                cursor.execute("""SELECT about FROM users WHERE user_id=?""", (item,))
                description = cursor.fetchone()
                description = description[0]

                surnames = f"{surnames}{surname}_SEPARATOR_"
                pfps = f"{pfps}{pfp}_SEPARATOR_"
                descriptions = f"{descriptions}{description}_MATCHES_"

            pendingfriendlist = f"displaypendingrequests('{user_ids}', '{forenames}', '{surnames}', '{pfps}', '{descriptions}')"


            user_ids = ""
            forenames = ""
            surnames = ""
            pfps = ""
            descriptions = ""

            for item in user_data3:
                user_ids = f"{user_ids}{item}_SEPARATOR_"

                cursor.execute("""SELECT forename FROM users WHERE user_id =?""", (item,))
                forename = cursor.fetchone()
                try:
                    forename = forename[0]
                except:
                    continue

                forenames = f"{forenames}{forename}_SEPARATOR_"


                cursor.execute("""SELECT surname FROM users WHERE user_id =?""", (item,))
                surname = cursor.fetchone()
                surname = surname[0]

                cursor.execute("""SELECT profile_picture FROM users WHERE user_id =?""", (item,))
                pfp = cursor.fetchone()
                pfp = pfp[0]

                cursor.execute("""SELECT about FROM users WHERE user_id=?""", (item,))
                description = cursor.fetchone()
                description = description[0]

                surnames = f"{surnames}{surname}_SEPARATOR_"
                pfps = f"{pfps}{pfp}_SEPARATOR_"
                descriptions = f"{descriptions}{description}_MATCHES_"


            cursor.execute("""SELECT about FROM users WHERE user_id =?""", (user_id,))
            about = cursor.fetchone()
            about = about[0]

            var1 = "')"
            var2 = "insertdesc('"

            about = f"{var2}{about}{var1}"



            friendlist = f"displayfriends('{user_ids}', '{forenames}', '{surnames}', '{pfps}', '{descriptions}')"

            conn.close()

            photoalbum = ""

            try:
                if typeofthing == "posts":
                    post_ids = ""
                    names = ""
                    messages = ""
                    user_ids = ""
                    profile_pictures = ""
                    likes = ""
                    dislikes = ""
                    comments_amounts = ""
                    photos = ""
                    times = ""
                    likers = ""
                    dislikers = ""
                    replying_to = ""

                    db_path = os.path.join(os.getcwd(), 'friendface.db')
                    conn2 = sqlite3.connect(db_path)
                    cursor2 = conn2.cursor()


                    cursor2.execute("""SELECT * FROM posts WHERE user_id = ?""", (user_id,))
                    posts = cursor2.fetchall()


                    photoalbum = "photoalbum('')"



                    for post in posts:
                        for column_name, value in zip(cursor2.description, post):


                            if column_name[0] == "post_id":
                                post_ids = f"{post_ids}{value}_SEPARATOR_"
                            if column_name[0] == "name":
                                names = f"{names}{value}_SEPARATOR_"
                            if column_name[0] == "message":
                                messages = f"{messages}{value}_SEPARATOR_"
                            if column_name[0] == "user_id":
                                user_ids = f"{user_ids}{value}_SEPARATOR_"
                            if column_name[0] == "profile_picture":
                                profile_pictures = f"{profile_pictures}image_SEPARATOR_"
                            if column_name[0] == "likes":
                                likes = f"{likes}{value}_SEPARATOR_"
                            if column_name[0] == "dislikes":
                                dislikes = f"{dislikes}{value}_SEPARATOR_"
                            if column_name[0] == "comments_amounts":
                                comments_amounts = f"{comments_amounts}{value}_SEPARATOR_"
                            if column_name[0] == "is_photo":
                                if value != "no":
                                    print("THIS IS A PHOTO")
                                    print("THIS IS A PHOTO")
                                    print("THIS IS A PHOTO")

                                    photos = f"{photos}image_SEPARATOR_"
                                else:
                                    photos = f"{photos}_SEPARATOR_"
                                    print("THIS IS NOT NOT NOT A PHOTO")
                                    print("THIS IS NOT NOT NOT A PHOTO")
                                    print("THIS IS NOT NOT NOT A PHOTO")


                            if column_name[0] == "time":
                                times = f"{times}{value}_SEPARATOR_"
                            if column_name[0] == "likers":
                                likers = f"{likers}{value}_SEPARATOR_"
                            if column_name[0] == "dislikers":
                                dislikers = f"{dislikers}{value}_SEPARATOR_"
                            if column_name[0] == "replying_to":
                                replying_to = f"{replying_to}{value}_SEPARATOR_"


                    posts = f"displayposts('{post_ids}', '{names}', '{messages}', '{user_ids}', '{profile_pictures}', '{likes}', '{dislikes}', '{comments_amounts}', '{photos}', '{times}', '{likers}', '{dislikers}', '{replying_to}', {current_user.id})"









                    conn2.close()
                else:
                    posts = ""





            except:
                posts = ""

            newposts = f"newpost('{current_user.forename} {current_user.surname}', '{profile_picture}', '{current_user.id}')"





            def user_profile2(filename):
                return render_template(filename, theirname=name, theirid = user_id, forename = current_user.forename, surname = current_user.surname,
                                        theirpicture=profile_picture, profile_picture=userdata,
                                        profile_text=name2, logo=logo, theirbanner=banner,
                                        user_id = user_id1, splashmessage = splash, followers = followers, friends = friends, onclick = onclick,
                                        pendingfriendlist = pendingfriendlist, friendlist = friendlist, about = about, displayposts = posts, followbuttonmessage = followbuttonmessage,
                                        followbuttonstate = followbuttonstate, friendbuttonmessage = friendbuttonmessage, photoalbum = photoalbum,
                                        onclickfriend = onclickfriend)

            def your_user_profile(filename):
                return render_template(filename, theirname=name, theirid = user_id, forename = current_user.forename, surname = current_user.surname, about = about,
                                        theirpicture=profile_picture, profile_picture=userdata,
                                        profile_text=name2, logo=logo, theirbanner=banner,
                                        user_id = user_id1, splashmessage = splash, followers = followers, friends = friends,
                                        pendingfriendlist = pendingfriendlist, friendlist = friendlist, displayposts = posts, newposts = newposts, photoalbum = photoalbum)


            if user_id != user_id1:
                if typeofthing == "posts":
                    return user_profile2("user_profile.html")
                elif typeofthing == "about":
                    return user_profile2("user_profile_ABOUT.html")
                elif typeofthing == "friends":
                    return user_profile2("user_profile_FRIENDS.html")
                elif typeofthing == "photos":
                    return user_profile2("user_profile_PHOTOS.html")
                else:
                    pass
            else:
                if typeofthing == "posts":
                    return your_user_profile("YOUR_user_profile.html")
                elif typeofthing == "about":
                    return your_user_profile("YOUR_user_profile_ABOUT.html")
                elif typeofthing == "friends":
                    return your_user_profile("YOUR_user_profile_FRIENDS.html")
                elif typeofthing == "photos":
                    return your_user_profile("YOUR_user_profile_PHOTOS.html")
                else:
                    pass


    except sqlite3.Error:
        raise
    finally:
        conn.close()





@app.route('/check', methods=['POST'])
def check_data():
    email = request.form['email']
    password = request.form['password']

    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""SELECT * FROM users WHERE email=?""", (email.lower(),))
        user_data = cursor.fetchone()

        if user_data and checkpw(password.encode('utf-8'), user_data[4]):
            user = User(user_data[0], user_data[1], user_data[2], user_data[3], user_data[4], user_data[5])
            login_user(user)
            print("yayyyyyy!!!!!!!!")
            return redirect(url_for('home', mode="feed"))
        else:
            return redirect(url_for('index2'))

    except sqlite3.Error:
        return redirect(url_for('index2'))
    finally:
        conn.commit()
        conn.close()



@app.route('/view/<int:post_id>', methods=['POST'])
def view(post_id):
    db_path = os.path.join(os.getcwd(), 'friendface.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""UPDATE posts SET views=views+1 WHERE post_id=?""", (post_id,))


        return "biggle"


    except sqlite3.Error:
        return redirect(url_for('index2'))
    finally:
        conn.commit()
        conn.close()








if __name__ == "__main__":
    app.run(port=5500, debug=True)
