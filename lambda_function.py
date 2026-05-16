import boto3
import json
import urllib3

# Initialize the AWS service clients globally for execution re-use
ssm = boto3.client('ssm')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('BloodStock')  # Matches your exact DynamoDB table name
http = urllib3.PoolManager()

def lambda_handler(event, context):
    try:
        api_key = ssm.get_parameter(Name='/bloodbank/api_key', WithDecryption=True)['Parameter']['Value']
        resource_id = "fced6df9-a360-4e08-8ca0-f283fc74ce15"
        url = f"https://data.gov.in{resource_id}?api-key={api_key}&format=json"
        
        print("Initializing ingestion workflow from Data.gov.in API...")
        
        response = http.request('GET', url)
        raw_payload = response.data.decode('utf-8').strip()
        if not raw_payload:
            print("CRITICAL: Received empty response string from the endpoint.")
            return {'statusCode': 400, 'body': "API endpoint issued an empty response layout."}
            
        data = json.loads(raw_payload)
        records = data.get('records', [])

        if not records:
            print("WARNING: API authenticated successfully but zero medical records were extracted.")
            return {'statusCode': 200, 'body': "Sync completed. No records returned by source."}

        count = 0
        with table.batch_writer() as batch:
            for r in records:
                # Extract identifiers to form unique composite Sort Keys
                h_name = r.get('_blood_bank_name', 'Unknown')
                pincode = str(r.get('pincode', '000000'))
                if not r.get('_latitude') or not r.get('_longitude'):
                    continue
                batch.put_item(
                    Item={
                        'District': r.get('_district', 'Unknown'),          # Partition Key
                        'blood_bank_name': h_name,                           # Base Identity Key
                        'hospital_blood_id': f"{h_name}_{pincode}",         # Composite unique identifier
                        'latitude': str(r.get('_latitude', '0')),            # Normalized geo string
                        'Longitude': str(r.get('_longitude', '0')),          # Capitalized string attribute
                        'Pincode': pincode,                                  # Normalized string
                        'City': r.get('_city', 'N/A'),
                        'Address': r.get('_address', 'N/A'),
                        'contact_mobile': r.get('_mobile') or r.get('_contact_no', 'N/A'),
                        'Category': r.get('_category', 'Private'),
                        'Blood Component Available': r.get('_blood_component_available', 'N/A'),
                        'Apheresis': r.get('_apheresis', 'N/A'),
                        'Service Time': r.get('_service_time', 'N/A'),
                        'Contact Nodal Officer': r.get('_contact_nodal_officer', 'N/A'),
                        'Email': r.get('_email', 'N/A'),
                        'Email Nodal Officer': r.get('_email_nodal_officer', 'N/A'),
                        'Fax': r.get('_fax', 'N/A'),
                        'Mobile Nodal Officer': r.get('_mobile_nodal_officer', 'N/A'),
                        'Nodal Officer': r.get('_nodal_officer_', 'N/A'),
                        'Qualification Nodal Officer': r.get('_qualification_nodal_officer', 'N/A'),
                        'renewal_date': r.get('_date_of_renewal', 'N/A'),
                        'Sr No': str(r.get('sr_no', '0')),
                        'State': r.get('_state', 'Unknown'),
                        'Date License Obtained': r.get('_date_license_obtained', 'N/A')
                    }
                )
                count += 1
            
        print(f"Data ingestion loop finished. Successfully persisted {count} units to DynamoDB.")
        return {
            'statusCode': 200,
            'body': json.dumps(f"Backend Sync Successful. Registered {count} storage facilities.")
        }

    except json.JSONDecodeError as json_err:
        print(f"JSON Parsing Exception caught: {str(json_err)}")
        return {'statusCode': 500, 'body': f"Failed to parse source layout: {str(json_err)}"}
    except Exception as e:
        print(f"Unhandled operational engine runtime failure: {str(e)}")
        return {'statusCode': 500, 'body': f"Pipeline Interrupted: {str(e)}"}
