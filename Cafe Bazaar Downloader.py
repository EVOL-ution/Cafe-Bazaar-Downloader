import re
import requests
from loguru import logger

logger.add("app.log", rotation="1 week")


def extract_package_name(url):
    regex = r"https://cafebazaar\.ir/app/(?:\?id=)?([\w.-]+)"
    match = re.search(regex, url)
    if match:
        app_name = match.group(1)
        return app_name
    else:
        logger.error("Invalid URL format: {}", url)
        raise ValueError("Invalid URL format")


def get_app_info(package_name):
    url = 'https://api.cafebazaar.ir/rest-v1/process/AppDetailsV2Request'
    payload = {
        "properties": {
            "androidClientInfo": {
                "sdkVersion": 22
            }
        },
        "singleRequest": {
            "appDetailsV2Request": {
                "packageName": package_name
            }
        }
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        try:
            app_details = data['singleReply']['appDetailsV2Reply']['meta']
            app_name = app_details['name']
            description = app_details.get('description', 'N/A')
            average_rate = app_details['reviewInfo']['averageRate']
            category = app_details['category']['name']
            install_count_range = app_details['installCount']['range']
            last_updated = data['singleReply']['appDetailsV2Reply']['package']['lastUpdated']

            logger.info("App info retrieved successfully for package: {}", package_name)
            return app_name, description, average_rate, category, install_count_range, last_updated
        except KeyError:
            logger.error("Unexpected API response format for package: {}", package_name)
            raise ValueError("Unexpected API response format")
    else:
        logger.error("Connection error with status code: {}", response.status_code)
        raise ValueError(f"Connection error with status code: {response.status_code}")


def call_download_api(pkg, sdk, retry=True):
    payload = {
        "properties": {
            "language": 2,
            "clientVersionCode": 1100301,
            "androidClientInfo": {
                "sdkVersion": sdk,
                "cpu": "x86,armeabi-v7a,armeabi",
            },
            "clientVersion": "11.3.1",
            "isKidsEnabled": False,
        },
        "singleRequest": {
            "appDownloadInfoRequest": {
                "downloadStatus": 1,
                "packageName": pkg,
                "referrers": [],
            },
        },
    }

    response = requests.post("https://api.cafebazaar.ir/rest-v1/process/AppDownloadInfoRequest", json=payload)
    if response.ok:
        data = response.json()
        logger.info("API call successful for package: {}", pkg)
        return handle_response(data)
    else:
        logger.error("API request failed for package: {}", pkg)

        if retry and sdk != 25:
            logger.info("Retrying with SDK version 25 for package: {}", pkg)
            return call_download_api(pkg, 25, retry=False)
        else:
            logger.error("Abnormal API response for package: {}", pkg)
            raise ValueError("Abnormal API response. Check your request and try again.")


def handle_response(data):
    app_info = data.get("singleReply", {}).get("appDownloadInfoReply")
    if not app_info:
        logger.error("Response does not include expected data")
        raise ValueError("Response does not include expected data")

    download_urls = app_info.get("fullPathUrls", [])
    if not download_urls:
        logger.error("Download URLs are empty")
        raise ValueError("Download URLs are empty")

    file_size = int(app_info.get("packageSize", 0)) / 1024 / 1024
    version_code = app_info.get("versionCode", 0)

    return download_urls[-1], file_size, version_code


if __name__ == "__main__":
    try:
        url = input("Enter the current URL: ")
        logger.info("User entered URL: {}", url)

        package_name = extract_package_name(url)
        app_name, description, average_rate, category, install_count_range, last_updated = get_app_info(package_name)
        download_link, file_size, version_code = call_download_api(package_name, 33)

        logger.info("App information retrieved successfully for package: {}", package_name)
        logger.info("Download link: {}", download_link)

        print("App Name:", app_name)
        print("Description:", description)
        print("Average Rate:", average_rate)
        print("Category:", category)
        print("Install Count Range:", install_count_range)
        print("Last Updated:", last_updated)
        print("Extracted Package Name:", package_name)
        print("Download link:", download_link)
        print(f"File size: {file_size:.2f} MB")
        print("Version:", version_code)

    except Exception as e:
        logger.exception("An error occurred: {}", str(e))
        print("An error occurred:", str(e))
