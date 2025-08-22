import cloudinary
import cloudinary.uploader

# Config
cloudinary.config( 
    cloud_name = "dhcoujnz7", 
    api_key = "798579394835414", 
    api_secret = "EJZoxcUeE6YAzyObZClpstGL9wU", 
    secure=True
)

# Upload local image
upload_result = cloudinary.uploader.upload(r"H:\Rich_Internship\FastApi2\instagram\uploads\bfocus.jpg", public_id="test_post")

# Yeh milega output me ek URL
print(upload_result["secure_url"])
