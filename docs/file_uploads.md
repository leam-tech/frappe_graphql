## File Uploads

File uploads can be done following the [GraphQL multipart request specification](https://github.com/jaydenseric/graphql-multipart-request-spec). `uploadFile` mutation is included implementing the same

### Query

```http
POST /api/method/graphql HTTP/1.1
Host: test_site:8000
Accept: application/json
Cookie: full_name=Administrator; sid=<sid>; system_user=yes; user_id=Administrator; user_image=
Content-Length: 553
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW

----WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="operations"

{
  "query": "mutation uploadFile($file: Upload!) { uploadFile(file: $file) { name, file_url  } }",
  "variables": {
    "file": null
  }
}
----WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="map"

{ "0": ["variables.file"] }
----WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="0"; filename="/D:/faztp12/Pictures/BingImageOfTheDay_20190715.jpg"
Content-Type: image/jpeg

(data)
----WebKitFormBoundary7MA4YWxkTrZu0gW
```

Response

```json
{
  "data": {
    "uploadFile": {
      "name": "ce36b2e222",
      "file_url": "/files/BingImageOfTheDay_20190715.jpg"
    }
  }
}
```
