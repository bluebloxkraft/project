"""
Music catalogue with a simple rating system
"""

import mysql.connector as mc
import datetime
import webbrowser
import random
import matplotlib.pyplot as plt

conn = None
cur = None

# queue of queries made with admin menu which can be commited
changes_made = []

def main():
    global conn

    print("="*15, "LOGIN MENU", "="*15)
    print("1 - use as guest")
    print("2 - login as admin")
    print()

    ch = input("Enter option: ")

    if ch == "1":
        try:
            conn = mc.connect(
                host="localhost",
                user="guest",
                password="guestpassword",
                database="music_project",
                charset="utf8"
            )
        except:
            print("Something went wrong")
            return

        try:
            user_menu()
        except KeyboardInterrupt:
            print("Exiting...")
            cur.close()
            conn.close()
            return
    elif ch == "2":
        pw = input("Enter admin password: ")

        try:
            conn = mc.connect(
                host="localhost",
                user="admin",
                password=pw,
                database="music_project",
                charset="utf8"
             )
        except:
            print("Something went wrong (possibly incorrect password)")
            return

        try:
            admin_menu()
        except KeyboardInterrupt:
            print("Exiting...")
            cur.close()
            conn.close()
            return

    else:
        print("Invalid option")

def user_menu():
    global cur

    cur = conn.cursor()

    while True:
        print("="*15, "MENU", "="*15)
        print("1 - show all songs")
        print("2 - search a song by title")
        print("3 - search a song by artist")
        print("4 - show top 10 highest rated songs")
        print("5 - exit")
        print()

        ch = input("Enter option: ")

        if ch == "1":
            show_all()
        elif ch == "2":
            search_by_title()
        elif ch == "3":
            search_by_artist()
        elif ch == "4":
            show_top_rated_graph()
        elif ch == "5":
            print("Exiting...")
            cur.close()
            conn.close()
            break
        else:
            print("Invalid option")

def show_all():
    q1 = "SELECT title, artist, duration FROM music ORDER BY title"
    q2 = "SELECT url, id FROM music ORDER BY title"
    selection_menu(q1, q2)

def search_by_title():
    title = input("Enter a song title: ")

    q1 = f'SELECT title, artist, duration FROM music WHERE title LIKE "%{title}%" ORDER BY title'
    q2 = f'SELECT url, id FROM music WHERE title LIKE "%{title}%" ORDER BY title'
    selection_menu(q1, q2)

def search_by_artist():
    artist = input("Enter an artist's name: ")

    q1 = f'SELECT title, artist, duration FROM music WHERE artist LIKE "%{artist}%" ORDER BY title'
    q2 = f'SELECT url, id FROM music WHERE artist LIKE "%{artist}%" ORDER BY title'
    selection_menu(q1, q2)

def show_top_rated_graph():
    q = "SELECT title, artist, rating FROM music NATURAL JOIN ratings ORDER BY ratings.rating DESC;"
    cur.execute(q)

    # only get first 10 for top 10 rated songs
    # order then reversed so the the bar
    # of the highest rated one is on top and such
    table = cur.fetchall()[0:10][::-1]
    songs = [f"{x[0]}\nby {x[1]}" for x in table]
    ratings = [x[2] for x in table]

    # matplotlib horizontal bar graph
    plt.barh(songs, ratings, color="skyblue")
    plt.xlabel("Rating (avg)", fontsize=7)
    plt.ylabel("Songs", fontsize=7)
    plt.xticks(fontsize=5)
    plt.yticks(fontsize=5)
    plt.title("Top 10 Highest Rated Songs")

    plt.show()

# this function takes two queries one for retrieving the actual table used to display
# to the user and the other for the corresponding URLs and IDs
# the titles parameter is the list of stylised column names displayed to the user
# and it has the default value given in the function definition
def selection_menu(q1, q2, titles=["Title", "Artist(s)", "Duration"]):
    cur.execute(q1)
    table = cur.fetchall()
    cur.execute(q2)
    urls_and_ids = cur.fetchall()

    if len(table) == 0:
        print("Table is empty")
        return

    if len(table) != len(urls_and_ids):
        raise Error("Number of rows and number of URLs/IDs don't match")

    table_numbered = []

    for i in range(len(table)):
        # gives new table with serial nums in the first column
        table_numbered.append([str(i)] + list(table[i]))

    print_table(table_numbered, ["No."] + titles)
    print()

    while True:
        ch = input("Enter number to open (n for none): ")

        if ch in "Nn":
            print("Quiting selection...")
            return

        found = False

        for i in range(len(table_numbered)):
            if ch == table_numbered[i][0]:
                found = True
                interact_song(urls_and_ids[i][0], urls_and_ids[i][1])
                break

        if found:
            break

        print("Invalid number")

        retry = input("Retry? (Y/n): ")

        # quit if user enters n or N
        # the second condition ensures this since an empty
        # string satisfies the first condition too
        if retry in "Nn" and retry != "":
            print("Quiting selection...")
            break

def interact_song(url, uid):
    while True:
        print("1 - open song")
        print("2 - rate song")
        print("3 - quit menu")
        print()

        ch = input("Enter option: ")

        if ch == "1":
            print(f"Opening {url} in web browser")

            # open in a new tab
            webbrowser.open(url, new=2, autoraise=True)
            break
        elif ch == "2":
            r = input("Enter rating (0-5): ")

            if not r.isdecimal() or not 0 <= int(r) <= 5:
                print("Rating must be an integer from 0 to 5")
                continue

            # q1 sets the new avg rating
            # q2 updates the number of ratings
            q1 = f"UPDATE ratings SET rating=(rating * rate_no + {r}) / (rate_no+1) WHERE id='{uid}'"
            q2 = f"UPDATE ratings SET rate_no=rate_no + 1 WHERE id='{uid}'"
            cur.execute(q1)
            conn.commit()
            cur.execute(q2)
            conn.commit()
            break
        elif ch == "3":
            print("Quitting selection...")
            break
        else:
            print("Invalid option")

def admin_menu():
    global cur
    cur = conn.cursor()

    while True:
        print("="*15, "ADMIN MENU", "="*15)
        print("1 - add song")
        print("2 - modify song")
        print("3 - remove song")
        print("4 - commit changes")
        print("5 - discard changes")
        print("6 - exit")
        print()

        ch = input("Enter option: ")

        if ch == "1":
            add_song()
        elif ch == "2":
            modify_song()
        elif ch == "3":
            remove_song()
        elif ch == "4":
            commit_changes()
        elif ch == "5":
            discard_changes()
        elif ch == "6":
            print("Exiting...")
            cur.close()
            conn.close()
            break
        else:
            print("Invalid choice")

def add_song():
    title = input("Enter the title: ").replace("\"", "\\\"")
    artist = input("Enter the artists: ")
    dur = input("Enter the duration (h:mm:ss): ")
    url = input("Enter the URL: ")
    uid = gen_uid()

    q1 = f"INSERT INTO music VALUES('{uid}', '{title}', '{artist}', '{dur}', '{url}')"
    q2 = f"INSERT INTO ratings VALUES('{uid}', 0, 0)"
    changes_made.append(q1)
    changes_made.append(q2)

def modify_song():
    cur.execute("SELECT * FROM music")
    table = cur.fetchall()
    print_table(table, ["ID", "Title", "Artist(s)", "Duration", "URL"])

    properties = ["title", "artist", "duration", "url"]

    uid = input("Enter ID of the song entry: ")
    ch = input("Which property to change?: ")

    if ch not in properties:
        print("Invalid property. Must be title, artist, duration or url")
        return

    val = input("Enter new value: ").replace("\"", "\\\"")

    q = f"UPDATE music SET {ch}='{val}' WHERE id='{uid}'"
    changes_made.append(q)

def remove_song():
    cur.execute("SELECT * FROM music")
    table = cur.fetchall()
    print_table(table, ["ID", "Title", "Artist(s)", "Duration", "URL"])

    uid = input("Enter ID of the song entry: ")

    q1 = f"DELETE FROM music WHERE ID='{uid}'"
    q2 = f"DELETE FROM ratings WHERE ID='{uid}'"
    changes_made.append(q1)
    changes_made.append(q2)

def commit_changes():
    ch = input("Enter are you sure? (y/N): ")

    if ch not in "Yy" and ch != "":
        print("Not committing changes")
        return

    print("Committing changes...")

    while changes_made != []:
        q  = changes_made.pop(0)
        cur.execute(q)
        conn.commit()

def discard_changes():
    ch = input("Enter are you sure? (y/N): ")

    if ch not in "Yy" and ch != "":
        print("Not discarding changes")
        return

    changes_made.clear()
    print("Changes discarded")

# this function generates a unique ID for a song entry
# consisting of random alphabets and digits
def gen_uid():
    chars = "abcdefghijklomnpqrstuvwxyz1234567890"

    result = ""

    for _ in range(16):
        result += chars[random.randrange(len(chars))]

    return result

# this function is used to print the table return by MySQL
# it takes the table data given by fetchall() and prints it in the same
# table format as MySQL does
def print_table(table_raw, titles):
    if len(titles) == 0:
        raise ValueError("'titles' can not be []")

    if len(table_raw) == 0:
        print("Table is empty")
        return

    col_lengths = []

    table = []

    for r in table_raw:
        L = []
        for c in r:
            # this checks if c is of type datetime.timedelta
            # (given by the "duration" column)
            # and if it is also less than 1 hour, it removes first two chars
            # for eg., 0:04:39 becomes 04:39
            if type(c) == datetime.timedelta and c.total_seconds() < 3600:
                L.append(str(c)[2::])
            else:
                L.append(str(c))
        table.append(L)

    for t in titles:
        if type(t) != str:
            raise TypeError("the values in 'titles' must be strings")

        # set the column lengths
        col_lengths.append(len(t))

    len_cl = len(col_lengths)

    # checks the num of cols of first row which is same as the rest
    if len(table[0]) != len(titles):
        raise ValueError("'titles' must the same number of elements as the table columns")

    # this loops through all rows and increments the column lengths
    # if a value is found greater than the already specified lengths in
    # col_lengths
    for r in table:
        for i in range(len_cl):
            if len(r[i]) > col_lengths[i]:
                col_lengths[i] = len(r[i])

    # this makes the border
    # eg: +----+------------+------+
    # n+2 to account for a 1 space gap between titles and the vertical bars
    horiz_border = "+" + "+".join(["-"*(n+2) for n in col_lengths]) + "+\n"

    # the resultant output
    res = horiz_border

    # all title appended with padding spaces
    padded_titles = [f"{titles[i]:{col_lengths[i]}}" for i in range(len_cl)]
    # the titles eg | artist | title | url |
    res += "| " + " | ".join(padded_titles) + " |\n"
    res += horiz_border

    for r in table:
        padded_columns = [f"{r[i]:{col_lengths[i]}}" for i in range(len_cl)]
        res += "| " + " | ".join(padded_columns) + " |\n"

    res += horiz_border

    print(res)

# run the main() function
main()
