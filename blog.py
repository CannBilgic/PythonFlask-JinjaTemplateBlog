from unittest import result
from flask import Flask,render_template,request,flash,redirect,url_for,logging,session
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
import psycopg2
from functools import wraps

#kullanıcı giriş decarotor
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için giriş yapınız..!","danger")
            return redirect(url_for("login"))
        
    return decorated_function

#kullanıcı kayıt form
class RegisterForm(Form):
    name = StringField('İsim Soyisim', validators=[validators.Length(min=4,max=25)])
    username = StringField('Kullanici Adi', validators=[validators.Length(min=4,max=35)])
    email = StringField('Email Adresi', validators=[validators.Email(message="Lütfen Geçerli Bir Email Giriniz.")])
    password=PasswordField('Parola',validators=[validators.DataRequired(message="Lütfen Bir parola belirleyiniz."),validators.EqualTo(fieldname="confirm",message="Parolalar Uyuşmuyor")])
    confirm = PasswordField('Parolayı Tekrar Giriniz.')
app=Flask(__name__)
app.secret_key="ybblog"
db= psycopg2.connect(user="postgres",password="12345",host="localhost",port="5432",database="Python")




@app.route("/")
def index():
    numbers =[1,2,3,4,5]
    return render_template("index.html",numbers=numbers)

#kayıt olma
@app.route("/register",methods=["GET","POST"])
def register():
    form= RegisterForm(request.form)

    if request.method== "POST" and form.validate():
        name=form.name.data
        username=form.username.data
        email=form.email.data
        #parolayı şifreli şekilde gönderiyor
        password=sha256_crypt.encrypt(form.password.data)

        sorgu="Insert into users(name,email,username,password) Values(%s,%s,%s,%s)"
        cursor=db.cursor()
        cursor.execute(sorgu,(name,email,username,password))
        db.commit()
        cursor.close()
        flash("İslem Başarılı...","success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form=form)

class LoginForm(Form):
    username=StringField("Kullanıcı Adı",validators=[validators.Length(min=4,max=35)])
    password=PasswordField("Şifre")

#Login
@app.route("/login",methods=["GET","POST"])
def login():
    form=LoginForm(request.form)
    if request.method== "POST" :
        username=form.username.data
        password_entered=form.password.data
        cursor=db.cursor()
        sorgu = "select * from users  where  username = %s " 
        cursor.execute(sorgu,(username,))
        result=cursor.fetchone()
        print(result)
        try:
            if result[0] > 0  :
                real_password= result[4]
                print(real_password)
                if sha256_crypt.verify(password_entered,real_password):
                    flash("Başarıyla giriş yaptınız...","success")
                    session["logged_in"]= True
                    session["username"]=username
                    return redirect(url_for("index"))
                else:
                    flash("Parola hatalı...","danger")
                    return redirect(url_for("login"))

                
        except :
            flash("Böyle bir kullanıcı bulunmuyor...","danger")
            return redirect (url_for("login"))


    return render_template ("login.html",form=form)
#logout işlemi
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    cursor=db.cursor()
    sorgu="select * from articles where author = %s"
    cursor.execute(sorgu,(session["username"],))
    result=cursor.fetchone()
    print("DEĞİŞKEN TİPİ =",result)
    if result[0] > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles=articles)

    else:
        return render_template("dashboard.html")
    



@app.route("/about")
def about():
    return render_template("about.html")
#makale ekleme
@app.route("/addarticle",methods=["GET","POST"])
def addarticle():
    form=ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title=form.title.data
        content=form.content.data
        cursor=db.cursor()
        sorgu= "insert into articles(title,author,content) values (%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        db.commit()
        cursor.close()
        flash("Makale kayıdı başarılı","success")
        return redirect(url_for("dashboard"))


    return render_template("addarticle.html",form=form)
#makale form
class ArticleForm(Form):
    title=StringField("Makale Başlığı",validators=[validators.length(min=5 ,max=100)])
    content=TextAreaField("Makale İçeriği",validators=[validators.length(min=10)])
#makale silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor=db.cursor()
    sorgu ="select* from articles where author =%s and id = %s"
    cursor.execute(sorgu,(session["username"],id))
    result=cursor.fetchone()
    if result[0]>0:
        sorgu2="delete from articles where id= %s"
        cursor.execute(sorgu2,(id,))
        db.commit()
        return redirect(url_for("dashboard"))

    else:
        flash("Size ait makale değil ya da böyle bir makale yok","danger")
        return redirect(url_for("index"))


#makale sayfası listeleme
@app.route("/articles")
def article ():
    cursor= db.cursor()
    sorgu ="Select * from articles"
    cursor.execute(sorgu)
    result=cursor.fetchone()
    if result[0] > 0:
        articles=cursor.fetchall()
        return render_template("articles.html",articles=articles)
    else:
        return render_template("articles.html")



if __name__ == "__main__":
    app.run(debug=True)























