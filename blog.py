from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField,validators
from passlib.hash import sha256_crypt
import email_validator
from functools import wraps

# Kullanıcı Giriş Decorator #
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın veya kayıt olun!", "danger")
            return redirect(url_for("login"))
    return decorated_function


# Kullanıcı Kayıt Formu #

class registerForm(Form):
    name = StringField("İsim Soyisim: ",validators=[validators.Length(min = 4, max=25)])
    username = StringField("Kullanıcı Adı: ",validators=[validators.Length(min = 5, max=20,)])
    email = StringField("E-Mail: ",validators=[validators.Email(message="Lütfen Geçerli Bir E-Mail Adresi Girin!"),validators.data_required()])
    password = PasswordField("Parola: ",validators=[validators.Length(min = 4, max=25), validators.data_required(message="Lütfen bir parola girin!"),validators.EqualTo(fieldname="confirm", message="Parolanız uyuşmuyor")])
    confirm = PasswordField("Parola Doğrula: ")

# Kullanıcı Giriş Formu #

class loginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")


uygulama = Flask(__name__)
uygulama.secret_key = "ukbblog"

uygulama.config["MYSQL_HOST"] = "localhost"
uygulama.config["MYSQL_USER"] = "root"
uygulama.config["MYSQL_ PASSWORD"] = ""
uygulama.config["MYSQL_DB"] = "ukb blog"
uygulama.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(uygulama)




@uygulama.route("/") #http://localhost:5000
def index():
    articles = [
        {"id":1,"title": "deneme1", "content": "deneme1 içerik"},
        {"id":2,"title": "deneme2", "content": "deneme2 içerik"},
        {"id":3,"title": "deneme3", "content": "deneme3 içerik"}
        ]
    return render_template("index.html", articles = articles)



@uygulama.route("/about") #http://localhost:5000/about
def about():
    return render_template("about.html")

@uygulama.route("/about/umut") #http://localhost:5000/about/umut
def umut():
    return "Umut Kaan Boğan"

#Kayıt Olma
@uygulama.route("/register", methods = ["GET", "POST"])
def register():
    form = registerForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        
        sorgu = "Insert into users(name,email,username,password) VALUES(%s, %s, %s, %s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()

        cursor.close()

        flash("Başarıyla Kayıt Oldunuz, Lütfen Giriş Yapın!","success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html", form = form)

@uygulama.route("/login", methods = ["GET", "POST"])
def login():
    form = registerForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "Select * From users where username = %s"
        result = cursor.execute(sorgu,(username,))
        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla Giriş Yaptınız!","success")
                session["logged_in"] = True
                session["username"] = username
                
                return redirect(url_for("index"))

            else:
                flash("Parolanız Doğru Değil!", "danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunamadı!","danger")
            return redirect(url_for("login"))
        

    return render_template("login.html", form = form)

@uygulama.route("/logout")
def logout():
    session.clear()
    flash("Başarıyla Çıkış Yaptınız!","success")
    return redirect(url_for("index"))


@uygulama.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu= "SELECT * From articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles = articles)
    else:
        return render_template("dashboard.html")


#Makale Ekleme

@uygulama.route("/addarticle", methods= ["GET", "POST"])
@login_required
def add_article():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        cursor = mysql.connection.cursor()

        sorgu = "INSERT into articles(title,author,content) VALUES(%s,%s,%s) "
        
        cursor.execute(sorgu,(title,session["username"],content))
        
        mysql.connection.commit()
        
        cursor.close()
        flash("Makale Başarıyla Oluşturuldu!", "success")
        
        return redirect(url_for("dashboard"))
        
    return render_template("addarticle.html", form=form)
    


#Makale Form
class ArticleForm(Form):
    title = StringField("Makale Başlığı", validators=[validators.length(min = 5, max=100)])
    content = TextAreaField("Makale İçeriği", validators=[validators.length(min=10)])







#Makaleler
@uygulama.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * From articles"

    result = cursor.execute(sorgu)
    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles=articles)
    else:
        return render_template("articles.html")


#Detay Sayfası
@uygulama.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * From articles where id = %s"
    result = cursor.execute(sorgu,(id,))
    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html", article=article)
    else:
        return render_template("article.html")

#Makale Silme
@uygulama.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * From articles where author = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"], id ))

    if result > 0 :
        sorgu2 = "DELETE From articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()

        return redirect(url_for("dashboard"))

    else:
        flash("Böyle bir makale yok veya bu işleme yetkiniz yok!", "danger")
        return redirect(url_for("index"))

#Makale Güncelleme
@uygulama.route("/edit/<string:id>", methods=["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * From articles where id = %s and author =%s"
        result = cursor.execute(sorgu,(id,session["username"]))
        if result == 0:
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok!", "danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html", form=form)
        
    else:
        #POST REQUEST KISMI
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data
        sorgu2 = "UPDATE articles Set title = %s, content = %s where id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()
        flash("Makale başarıyla güncellendi!", "success")
        return redirect(url_for("dashboard"))

#Arama URL
@uygulama.route("/search", methods =["GET" , "POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * From articles where title like  '%" + keyword + "%'   "
        result = cursor.execute(sorgu)

        if result == 0:
            flash("Aranan kelimeye uygun makale bulunamadı!", "warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html", articles = articles)
        








if __name__ == "__main__":
    uygulama.run(debug=True)