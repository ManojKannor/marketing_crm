from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
import requests
import cloudinary
import cloudinary.uploader
import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()

# ---- Cloudinary Config ----
cloudinary.config( 
    cloud_name = "dhcoujnz7", 
    api_key = "798579394835414", 
    api_secret = "EJZoxcUeE6YAzyObZClpstGL9wU", 
    secure=True
)

LINKEDIN_ACCESS_TOKEN = "AQXL_EX70H7RK7WFEKoSdIaFMYi6QJ0QZqNEwHSJPvs00uYYLSd6n8sYqKHseO9obyBDtPKybdQXTskxd-g4UOnZpFjno50V9Cq_nEPaz-VkfPeu593_iLG_-QSkbttocKH7Yq1eUi4kXQ28y3HZRi_C_j87v-N3Q3ggbhseZ6UDW_sEmNli4y6l_VY0WXNr1yS9w6PIs0D2yd4JredzH7TAnKHxmV3LPikpXBAyHPgyEtDDWXFM8M8G_6EZA-ji3pfPq9CLmvVWr0j-CAcSsJzTAwxcWK-jWXVoc-OQAHs-LD4FX5cP7rkqqhpi4Fi9ThtW1GeAiPCafCg3-kHE58JS_oCgJQ" 

PERSON_URN = "urn:li:person:DJ1UpvC9dl"

INSTAGRAM_ACCESS_TOKEN = "EAATzBDJveQ8BPNnIY5NYxSj3OkUCU5u1HXc9qSJSzKZAyah2tVTFiTnew3ZA0N3bF0zQ0qJpOHEH6cr0TmRNJVZBoqasUnAjBkiSguOUlmSTP6AZBvK8rNQ3z9pfmtqeozLl7RTHhsdYeUx30HbsEommIjZC6r0Wo75ldrE4yLd6LZBtVohipZCejgCpTaI" 
INSTAGRAM_BUSINESS_ID = "17841476335499716"

# ---- Scheduler ----
scheduler = BackgroundScheduler()
scheduler.start()


# ---- UI Page ----
@app.get("/", response_class=HTMLResponse)
def form_page():
    return """
    <html>
        <body>
            <h2>Upload Post to LinkedIn + Instagram (Immediate / Scheduled)</h2>
            <form action="/upload" enctype="multipart/form-data" method="post">
                Caption: <input type="text" name="caption" /><br><br>
                Image: <input type="file" name="file" /><br><br>
                Schedule Time (YYYY-MM-DD HH:MM) [optional]: 
                <input type="datetime-local" name="schedule_time" />
                <input type="submit" value="Post"/>
            </form>
        </body>
    </html>
    """


# ---- Post Logic Function ----
def post_to_socials(caption, IMAGE_URL):
    linkedin_res = {}
    insta_res = {}

    # ---- LinkedIn ---- (NO scheduling support in API)
    try:
        register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
        register_body = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": PERSON_URN,
                "serviceRelationships": [
                    {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
                ]
            }
        }
        headers = {"Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}", "Content-Type": "application/json"}
        reg_res = requests.post(register_url, headers=headers, json=register_body).json()

        if "value" in reg_res:
            upload_url = reg_res["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
            asset = reg_res["value"]["asset"]

            img_data = requests.get(IMAGE_URL).content
            upload_headers = {"Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}", "Content-Type": "image/jpeg"}
            requests.put(upload_url, headers=upload_headers, data=img_data)

            post_url = "https://api.linkedin.com/v2/ugcPosts"
            post_body = {
                "author": PERSON_URN,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": caption},
                        "shareMediaCategory": "IMAGE",
                        "media": [{"status": "READY", "media": asset}]
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
            }
            linkedin_res = requests.post(post_url, headers=headers, json=post_body).json()
    except Exception as e:
        linkedin_res = {"error": str(e)}

    # ---- Instagram ---- (HAS scheduling support)
    try:
        create_url = f"https://graph.facebook.com/v23.0/{INSTAGRAM_BUSINESS_ID}/media"
        create_payload = {
            "image_url": IMAGE_URL,
            "caption": caption,
            "access_token" : INSTAGRAM_ACCESS_TOKEN
        }
        create_res = requests.post(create_url, data=create_payload).json()
        media_id = create_res.get("id")

        if media_id:
            publish_url = f"https://graph.facebook.com/v23.0/{INSTAGRAM_BUSINESS_ID}/media_publish"
            publish_payload = {
                "creation_id": media_id,
                "access_token": INSTAGRAM_ACCESS_TOKEN
            }
            insta_res = requests.post(publish_url, data=publish_payload).json()
    except Exception as e:
        insta_res = {"error": str(e)}

    return {
        "linkedin": linkedin_res,
        "instagram": insta_res
    }


# ---- Upload Endpoint ----
@app.post("/upload")
def upload(
    caption: str = Form(...),
    file: UploadFile = None,
    schedule_time: str = Form(None)
):
    try:
        # ---- Upload to Cloudinary ----
        upload_result = cloudinary.uploader.upload(
            file.file, public_id=file.filename.split(".")[0]
        )
        IMAGE_URL = upload_result["secure_url"]

        # ---- If schedule_time given ----
        if schedule_time:
            run_time = datetime.datetime.strptime(schedule_time, "%Y-%m-%dT%H:%M")

            # Schedule LinkedIn via APScheduler
            scheduler.add_job(post_to_socials, 'date', run_date=run_time, args=[caption, IMAGE_URL])

            # Schedule Instagram directly via Graph API param
            epoch_time = int(run_time.timestamp())
            create_url = f"https://graph.facebook.com/v23.0/{INSTAGRAM_BUSINESS_ID}/media"
            create_payload = {
                "image_url": IMAGE_URL,
                "caption": caption,
                "access_token": INSTAGRAM_ACCESS_TOKEN,
                "published": "false",
                "scheduled_publish_time": epoch_time   # <-- Instagram scheduling
            }
            insta_res = requests.post(create_url, data=create_payload).json()

            return JSONResponse(content={
                "status": "scheduled",
                "caption": caption,
                "image_url": IMAGE_URL,
                "linkedin": f"Scheduled for {schedule_time}",
                "instagram": insta_res
            })

        # ---- Else immediate post ----
        result = post_to_socials(caption, IMAGE_URL)
        return JSONResponse(content={
            "status": "posted",
            "caption": caption,
            "image_url": IMAGE_URL,
            **result
        })

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
