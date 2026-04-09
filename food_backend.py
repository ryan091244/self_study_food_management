from flask import Flask, redirect, url_for, render_template, request,flash
import pymongo
from googleapiclient.http import MediaIoBaseUpload
from pymongo import MongoClient
from bson.objectid import ObjectId
from Google import Create_Service
import io
from datetime import date
CLIENT_SECRET_FILE = "google_client_secret.json"
API_NAME = "drive"
API_VERSION = "v3"
SCOPE = ["https://www.googleapis.com/auth/drive"]
service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPE)
food_img_id = ""#這裡放我google drive用來存放圖片資料夾的id
cluster = MongoClient("")#這裡填資料庫的connection string
db = cluster["management"]
food_db = db["food"]
app = Flask(__name__)
app.secret_key=""#這裡自己想一個https加密用的金鑰
@app.route("/")
def home():
    return render_template("home.html")
@app.route("/delete/<item_id>",methods=["POST"])
def item_delete(item_id):
    item = food_db.find_one({"_id":ObjectId(item_id)})
    img_drive_id = item["img_google_id"]
    service.files().delete(fileId=img_drive_id).execute()
    food_db.delete_one({"_id":ObjectId(item_id)})
    flash("刪除成功","info")
    return redirect(url_for("home"))
@app.route("/edit/<item_id>")
def item_edit(item_id):
    item = food_db.find_one({"_id":ObjectId(item_id)})
    return render_template("item_edit.html",
    item_id = item_id,
    item_name=item["name"],
    item_exp_date=item["exp_date"],
    item_amount=item["amount"],
    item_remarks=item["remarks"],
    item_img_link=item["img_link"])
@app.route("/management/<page>")
def food_management(page):
    p=int(page)
    count = food_db.count_documents({})
    if 8+8*p < count:
        next = True
    else:
        next = False
    if p > 0:
        last = True
    else:
        last = False
    return render_template("food_management.html", display_list=food_db.find().sort({"exp_date":1}).limit(8+8*p).skip(8*p), web_page = p,n=next,l=last)
@app.route("/test")
def test():
    return render_template("test.html")
@app.route("/update/<item_id>",methods = ["POST"])
def update(item_id):
    item_id = ObjectId(item_id)
    food_db.update_one({"_id":item_id},{"$set":{"name":request.form["food_name"]}})
    food_db.update_one({"_id":item_id},{"$set":{"exp_date":request.form["exp_date"]}})
    food_db.update_one({"_id":item_id},{"$set":{"amount":request.form["food_amount"]}})
    food_db.update_one({"_id":item_id},{"$set":{"remarks":request.form["food_remarks"]}})
    flash("編輯成功","info")
    return redirect(url_for("home"))
@app.route("/upload",methods = ["POST","GET"])
def food_upload():
    if request.method == "POST" :  
        food_info = {
            "name" : request.form["food_name"],
            "exp_date" : request.form["exp_date"],
            "amount" : request.form["food_amount"],
            "remarks" : request.form["food_remarks"],
            "upload_date" : str(date.today())
        }
        food_object = food_db.insert_one(food_info)
        storage_img = request.files["food_img"]
        file_img = io.BytesIO(storage_img.stream.read())
        media = MediaIoBaseUpload(file_img,mimetype="image/jpeg")
        file_metadata = {
            "name" : [str(food_object.inserted_id)],
            "parents" : [food_img_id]
        }
        fields=service.files().create(
            body = file_metadata,
            media_body = media,
            fields = 'id'
        ).execute()
        food_db.update_one({"_id":food_object.inserted_id},{"$set":{"img_google_id":fields["id"]}})
        food_db.update_one({"_id":food_object.inserted_id},{"$set":{"img_link":"https://drive.google.com/thumbnail?id="+fields["id"]}})
        flash("上傳成功!","info")   
        return redirect(url_for("home"))       
    else :
        return render_template("food_upload.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0")
