import boto3
from botocore.config import Config

# R2 credentials (replace with your actual values)
R2_ENDPOINT = "https://abc123def456.r2.cloudflarestorage.com"
R2_ACCESS_KEY_ID = "1a2b3c4d5e6f7g8h9i0j"
R2_SECRET_ACCESS_KEY = "k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0"
R2_BUCKET_NAME = "helpuvio-datasets"

# Create S3 client
s3_client = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    config=Config(signature_version='s3v4')
)

# Test 1: List buckets
print("✅ Testing R2 connection...")
try:
    response = s3_client.list_buckets()
    print(f"✅ Connected! Found {len(response['Buckets'])} bucket(s)")
    for bucket in response['Buckets']:
        print(f"   - {bucket['Name']}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)

# Test 2: Upload test file
print("\n✅ Testing file upload...")
try:
    test_content = "company_name,company_email\nTest Company,test@example.com"
    s3_client.put_object(
        Bucket=R2_BUCKET_NAME,
        Key='test/test.csv',
        Body=test_content.encode('utf-8'),
        ContentType='text/csv'
    )
    print("✅ Upload successful!")
except Exception as e:
    print(f"❌ Upload failed: {e}")
    exit(1)

# Test 3: Generate signed URL
print("\n✅ Testing signed URL generation...")
try:
    url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': R2_BUCKET_NAME, 'Key': 'test/test.csv'},
        ExpiresIn=3600
    )
    print(f"✅ Signed URL generated:")
    print(f"   {url[:80]}...")
except Exception as e:
    print(f"❌ Signed URL failed: {e}")
    exit(1)

# Test 4: Delete test file
print("\n✅ Cleaning up...")
try:
    s3_client.delete_object(Bucket=R2_BUCKET_NAME, Key='test/test.csv')
    print("✅ Test file deleted")
except Exception as e:
    print(f"⚠️  Cleanup warning: {e}")

print("\n🎉 All R2 tests passed! Your configuration is correct.")
