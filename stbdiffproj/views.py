from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from .serializers import ImageSerializer
import psycopg2
import pandas as pd
import io
DB_HOST = "localhost"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_NAME = "localdata"

def store_data_in_db(data):
    """
    This function connects to a PostgreSQL database, extracts image and caption from data,
    creates a pandas DataFrame, stores it in a table, and closes the connection.

    Args:
        data: A dictionary containing the data to be stored.

    Returns:
        None
    """

    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME
        )
        cur = conn.cursor()
        # Check if the table exists and create if it does not
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stable_diff_table (
                id SERIAL PRIMARY KEY,
                dataframe BYTEA NOT NULL
            );
        """)
        # Extract image and caption
        extracted_data = []
        print(data)
        for item in data:

            extracted_data.append(
                {"image": item["image"], "caption": item["caption"][1:-1]}
            )

        # Create DataFrame
            df = pd.DataFrame(extracted_data)

            # Serialize and store in table
            dataframe_bytes = io.BytesIO()  # Create a memory buffer
            df.to_pickle(dataframe_bytes)  # Serialize to the buffer
            dataframe_bytes.seek(0)  # Rewind the buffer to read the serialized data
            serialized_bytes = dataframe_bytes.read()

            cur.execute(
                "INSERT INTO stable_diff_table (id, dataframe) VALUES (%s, %s);",
                (item["id"], serialized_bytes),  # Use the extracted bytes
            )
        conn.commit()

    except Exception as e:
        print(f"Error storing data: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Close connection
        if conn:
            conn.close()
class ImageUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        if request.method == "POST":    
            # Access uploaded files and captions
            images = request.FILES.getlist('images')
            captions_string = request.data.get('captions', '')
            captions = [caption.strip() for caption in captions_string.split(',') if caption]
            names_string = request.data.get('names', '')
            names= [name.strip() for name in names_string.split(',') if name]
            print(f"Uploading {len(images)} images with captions: {len(captions)}{type(captions)}.")

            # Validate number of captions matches images
            if len(images) != len(captions):
                print("Error: Number of captions does not match number of images.")
                return Response({'error': 'Number of captions must match number of images.'}, status=400)

            # Create and save image objects with captions
            image_objects = []
            for i, image in enumerate(images):
                print(f"Processing image {i+1}/{len(images)}")
                serializer = ImageSerializer(data={'name' : names[i],'image': image, 'caption': captions[i] if i < len(captions) else ''})
                if serializer.is_valid():
                    serializer.save()
                    image_objects.append(serializer.data)
                else:
                    print(f"Validation errors for image {i+1}: {serializer.errors}")
                    return Response(serializer.errors, status=400)
            data = image_objects # Access form data or API payload
            store_data_in_db(data)
            print("All images uploaded successfully.")
            return Response({'data': image_objects}, status=201)
