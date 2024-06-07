import boto3
import logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Specify the sender email address
SENDER_EMAIL = 'email@email.com'  # Replace with your verified SES email

def lambda_handler(event, context):
    ses = boto3.client('ses')
    iam = boto3.client('iam')

    try:
        # List all IAM users
        logger.info("Listing all IAM users...")
        users = iam.list_users()

        for user in users['Users']:
            username = user['UserName']
            logger.info(f"Checking access keys for user: {username}")
            
            # List access keys for the user
            keys = iam.list_access_keys(UserName=username)
            
            for key in keys['AccessKeyMetadata']:
                access_key_id = key['AccessKeyId']
                create_date = key['CreateDate']
                key_age = (datetime.now(timezone.utc) - create_date).days
                
                # Log access key information
                logger.info(f"Access key {access_key_id} for user {username} is {key_age} days old.")
                
                if key_age > 90:
                    # Get the user's email
                    email = get_user_email(username)
                    
                    if email:
                        # Log the retrieved email address
                        logger.info(f"Retrieved email for user {username}: {email}")
                        
                        # If the key is older than 90 days, send a notification to the user's email
                        message = f'User {username}, your access key {access_key_id} is {key_age} days old. Please rotate it.'
                        logger.info(f"Sending notification to {email}: {message}")
                        
                        # Send an email notification using SES
                        response = ses.send_email(
                            Source=SENDER_EMAIL,
                            Destination={
                                'ToAddresses': [email]
                            },
                            Message={
                                'Subject': {
                                    'Data': 'AWS Access Key Rotation Notification',
                                    'Charset': 'UTF-8'
                                },
                                'Body': {
                                    'Text': {
                                        'Data': message,
                                        'Charset': 'UTF-8'
                                    }
                                }
                            }
                        )
                        logger.info(f"Email sent! Message ID: {response['MessageId']}")
                    else:
                        logger.warning(f"No email found for user {username}")

        logger.info("Notifications sent successfully!")
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        raise

def get_user_email(username):
    iam = boto3.client('iam')
    # Placeholder function to retrieve the user's email
    try:
        response = iam.list_user_tags(UserName=username)
        logger.info(f"Tags for user {username}: {response['Tags']}")
        for tag in response['Tags']:
            if tag['Key'] == 'email':
                return tag['Value']
    except Exception as e:
        logger.error(f"Error retrieving email for user {username}: {e}")
    return None
