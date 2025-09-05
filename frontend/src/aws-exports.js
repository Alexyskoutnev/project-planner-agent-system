// Replace these values with your actual AWS Cognito configuration
// You'll get these after setting up Cognito in AWS Console

const awsconfig = {
  aws_project_region: 'us-east-1', // Change to your region
  aws_cognito_region: 'us-east-1', // Change to your region
  aws_user_pools_id: 'us-east-1_XXXXXXXXX', // Replace with your User Pool ID
  aws_user_pools_web_client_id: 'xxxxxxxxxxxxxxxxxxxxxxxxxx', // Replace with your App Client ID
  // oauth: {
  //   domain: 'your-project-planner-auth.auth.us-east-1.amazoncognito.com', // Replace with your domain
  //   scope: ['phone', 'email', 'openid', 'profile', 'aws.cognito.signin.user.admin'],
  //   redirectSignIn: 'http://localhost:3000/callback',
  //   redirectSignOut: 'http://localhost:3000',
  //   responseType: 'code' // or 'token', recommended is code
  // },
  // federationTarget: 'COGNITO_USER_POOLS',
  aws_cognito_username_attributes: ['email'],
  // aws_cognito_social_providers: ['GOOGLE'], // Enable Google SSO
  aws_cognito_signup_attributes: ['email'],
  aws_cognito_mfa_configuration: 'OFF',
  aws_cognito_mfa_types: ['SMS'],
  aws_cognito_password_protection_settings: {
    passwordPolicyMinLength: 8,
    passwordPolicyCharacters: []
  },
  aws_cognito_verification_mechanisms: ['email']
};

export default awsconfig;