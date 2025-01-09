# ZTH Alliance Back-End Code

## General design

Use Github's Pages service to use a repo to host a static website for free. Use Cloudflare CDN to shield and protect the site for free. Use AWS free tier services to add dynamic content to the website for free. Using a static website greatly reduces the attack surface from a cybersecurity perspective. We offload any dynamic server-side processing to AWS, letting them take the risk.

## General workflow

User goes to "https://zthalliance.com". They click on the "Spread the Word" link at the top of the page. The resulting page is a form that accepts any postal code, as it's not restricted to accepting a 5-digit US ZIP code. This gets submitted to an AWS Lambda function with the postal code submitted via GET, where the function uses an HTML template page stored in the website to substitute placeholder values, including a postal-code-specific QR code. This flyer page is designed to be fit on a single sheet of 8.5" x 11" paper. The user then prints this out and makes several printed copies. They then get a merchant to post the flyer in their storefront window. A customer who wants to spend honest money in that shop, upon seeing no honest money prices, scans the QR code, causing their mobile device to submit canned per-postal-code information to another Lambda function, which stores the data in a Dynamodb table. This allows the customer to cast their vote to encourage all merchants in that postal code to join the ZTH Alliance. The user then goes back to the website and clicks on the "Per-Postal-Code Customer Interest Stats" link at the top of the page, where all per-postal-code votes are tallied and displayed in descending order of total votes per postal code. The user can then wait for a certain time, like a month, then they can go back to merchants in that postal code area and show them the level of interest customers are showing in their area. This should hopefully be a least-effort way to gather actual customer interest stats that merchants can use to make an informed decision on whether or not to join the ZTH Alliance. This will then hopefully bring honest money prices for everyday necessities to that local community.

## Set up steps

Use Publii static website design software to create a static website and publish it to a Github repo. In the Github repo settings, enable Github Pages, so you can get Github to serve the content out as a website, for free. Register a custom domain name (ie. "zthalliance.com") somewhere like namecheap.com. Go to Cloudflare and set up DNS records per the Github Pages custom domain name guide. Point the registrar DNS server settings to Cloudflare in namecheap.com. Go to AWS, create a free tier account, set up Python Lambda functions, set up API Gateway to serve out the Lambda functions as API endpoints via GET. Set up Cloudflare WAF to rate limit access to the Lambda functions, so we don't get charged an arm and a leg if someone tries to abuse our API. Set up a Cloudflare Origin TLS certificate, import that into AWS Certificate Manager, and map that to the API Gateway as a custom DNS domain name. Doing this lets your free tier account expire, where the underlying, actual API Gateway "random"-style domain name becomes something predictable, so when our old AWS free tier account expires, you can simply set up a new AWS free tier account and nobody knows the difference. It also hides the fact that we're using AWS to power the dynamic portion of this web site.

## Publii

Publii needs additional files uploaded via the "File Manager" feature. Some of these files are HTML templates used by the Lambda functions. The "CNAME" file is required for the Github Pages custom domain name feature to work properly. All it contains is our custom domain name of "zthalliance.com". One file is our logo in transparent PNG format. This gets used by the flyer as externally available, included image content.

Publii > Tools & Plugins > File Manager

root directory:

CNAME
gather-postal-code-for-storefront-voting-flyer.html
storefront-postal-code-voting-flyer.html
storefront-postal-code-voting-response.html

media/files:

zth_alliance_logo_coins_transparent.png

NOTE: You also need to configure Publii to be able to upload your website pages to the Github repo supporting Github Pages to serve your website out:

Publii > Server > Github Pages

Website URL: https://zthalliance.com
API Server: api.github.com
Username: warelock2
Repository: zth_alliance
Branch: master
Token: (This must be your Github "Personal Access Token")

## DNS configuration

Cloudflare DNS configured per Github Pages Custom domain name DNS guidelines:

https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site

Cloudflare DNS record details:

A	zthalliance.com	185.199.108.153
A	zthalliance.com	185.199.109.153
A	zthalliance.com	185.199.110.153
A	zthalliance.com	185.199.111.153
CNAME	api	d-ry699nmpr4.execute-api.us-west-2.amazonaws.com
CNAME	www	zthalliance.com

NOTE: The value for api comes from creating an "Origin" TLS certificate in Cloudflare, which get imported into AWS Certificate Manager, and mapped to your API Gateway instance, per this guide:

https://medium.com/@amirhosseinsoltani7/connect-cloudflare-to-aws-api-gateway-c64f0713b5e9

When importing this into AWS certificate Manager, you'll also need the "Certificate Chain" portion from Cloudflare, here (documented in the guide in the link above):

https://developers.cloudflare.com/ssl/static/origin_ca_rsa_root.pem

NOTE: Make sure to set the SSL/TLS encryption mode to "Full (Strict)"

### Cloudflare Zone-level Web Application Firewall (WAF) rate limiting for our API

Rule name: api_rate_limit
Field: URI Path
Operator: wildcard
Value: https://api.zthalliance.com/*

Expression preview: (http.request.uri.path wildcard "https://api.zthalliance.com/*")

When rate exceeds: 10
Period: 10 seconds
Action: Block
Duration: 10 seconds

## AWS Lambda function environment variables

storefront-postal-code-voting-response:

DYNAMODB_TABLE: zth-alliance-customer-response
TEMPLATE_URL: https://zthalliance.com/storefront-postal-code-voting-response.html

---

storefront-postal-code-voting-results:

DYNAMODB_TABLE: zth-alliance-customer-response

---

storefront-postal-code-voting-flyer:

BASE_URL: https://api.zthalliance.com/storefront-postal-code-voting-response
TEMPLATE_URL: https://zthalliance.com/storefront-postal-code-voting-flyer.html

NOTE: The Lambda functions won't run without creating a "Layer", where you upload a "package" that contains support functions from requirements.txt.

echo "qrcode
Pillow
urllib3" > requirements.txt
mkdir package
vi package/lambda_function.py (Insert the Python code from the Lambda function)
pip install --platform manylinux2014_x86_64 --target=package --implementa
tion cp --python-version 3.13 --only-binary=:all: -r requirements.txt
zip -r ../deployment.zip .

NOTE: This creates a file called "deployment.zip", which you upload into the AWS Lambda function "Layer" you created earlier. This should only be redone if the requirements.txt changes. You'll know what to include if when you test your Lambda function it fails with a basic "Library X is missing"-type error. 

If you have to update the package directory because the requirements.txt file change, do this "pip install" command instead, adding "--upgrade" to the end:

pip install --platform manylinux2014_x86_64 --target=package --implementa
tion cp --python-version 3.13 --only-binary=:all: -r requirements.txt --upgrade

## AWS API Gateway

Name: template-service

GET endpoints:

/storefront-postal-code-voting-flyer
/storefront-postal-code-voting-response
/storefront-postal-code-voting-results

CORS configuration:

Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: *
Access-Control-Allow-Methods: GET

## AWS Dynamodb

Table name: zth-alliance-customer-response

Partition key: postal_code

Fields:

postal_code: String
visit_cound: Integer?

