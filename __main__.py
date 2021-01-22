"""Python Pulumi program for creating Google Cloud Functions.

Create a single Google Cloud Function. The deployed application will calculate
the estimated travel time to a given location, sending the results via SMS.
"""

import time
import os
import pulumi

from pulumi_gcp import storage
from pulumi_gcp import cloudfunctions

# File path to where the Cloud Function's source code is located.
PATH_TO_SOURCE_CODE = "./functions"
FUNCTION_RUNTIME = "python38"
FUNCTION_MEMORY_MB = 128

# Get values from Pulumi config.
config = pulumi.Config(name=None)
function_name = config.get("function_name")
function_entry_point = config.get("entry_point")
env_variables = {
    "MY_VAR": config.get("env_var"),
}

# We will store the source code to the Cloud Function in a Google Cloud Storage bucket.
bucket = storage.Bucket("%s_bucket" % function_name)

#archive = pulumi.AssetArchive(assets=assets)
archive = pulumi.AssetArchive({
    '.': pulumi.FileArchive(PATH_TO_SOURCE_CODE)
})

# Create the single Cloud Storage object, which contains all of the function's
# source code. ("main.py" and "requirements.txt".)
source_archive_object = storage.BucketObject(
    "%s_object" % function_name,
    name="main.py-%f.zip" % time.time(),
    bucket=bucket.name,
    source=archive)

# Create the Cloud Function, deploying the source we just uploaded to Google
# Cloud Storage.
fxn = cloudfunctions.Function(
    function_name,
    name=function_name,
    entry_point=function_entry_point,
    environment_variables=env_variables,
    runtime=FUNCTION_RUNTIME,
    available_memory_mb=FUNCTION_MEMORY_MB,
    source_archive_bucket=bucket.name,
    source_archive_object=source_archive_object.name,
    trigger_http=True)

invoker = cloudfunctions.FunctionIamMember(
    "invoker",
    project=fxn.project,
    region=fxn.region,
    cloud_function=fxn.name,
    role="roles/cloudfunctions.invoker",
    member="allUsers",
)

# Export the DNS name of the bucket and the cloud function URL.
pulumi.export("bucket_name", bucket.url)
pulumi.export("function_url", fxn.https_trigger_url)
