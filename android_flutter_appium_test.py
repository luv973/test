"""Appium automation for an Android Flutter app.

Steps covered:
1) Install APK, grant runtime permissions, and open app.
2) Run sample test cases against the launched app.

Usage:
    python android_flutter_appium_test.py \
      --apk /path/to/app-release.apk \
      --package com.example.app \
      --activity .MainActivity \
      --device emulator-5554

Prerequisites:
- Appium server running (default: http://127.0.0.1:4723)
- adb available in PATH
- Python packages: appium-python-client
"""

from __future__ import annotations

import argparse
import subprocess
import time
import unittest
from typing import Iterable

from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


def run_adb(device: str | None, args: Iterable[str]) -> subprocess.CompletedProcess:
    """Run an adb command and return the completed process."""
    base_cmd = ["adb"]
    if device:
        base_cmd += ["-s", device]
    full_cmd = base_cmd + list(args)
    return subprocess.run(full_cmd, check=True, capture_output=True, text=True)


def install_apk(device: str | None, apk_path: str) -> None:
    """Install (or reinstall) the APK on the target device."""
    run_adb(device, ["install", "-r", apk_path])


def grant_permissions(device: str | None, package_name: str, permissions: list[str]) -> None:
    """Grant Android runtime permissions declared by the app."""
    for permission in permissions:
        run_adb(device, ["shell", "pm", "grant", package_name, permission])


def launch_app(device: str | None, package_name: str, activity_name: str) -> None:
    """Launch the app using am start."""
    run_adb(device, ["shell", "am", "start", "-n", f"{package_name}/{activity_name}"])


class FlutterAndroidTests(unittest.TestCase):
    """Sample test cases for a Flutter Android app via Appium."""

    driver: webdriver.Remote
    wait: WebDriverWait

    @classmethod
    def setUpClass(cls) -> None:
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--appium-url", default="http://127.0.0.1:4723")
        parser.add_argument("--apk", required=True)
        parser.add_argument("--package", required=True)
        parser.add_argument("--activity", required=True)
        parser.add_argument("--device", default=None)
        parser.add_argument(
            "--permissions",
            nargs="*",
            default=[
                "android.permission.CAMERA",
                "android.permission.RECORD_AUDIO",
                "android.permission.ACCESS_FINE_LOCATION",
                "android.permission.ACCESS_COARSE_LOCATION",
            ],
        )
        args, _ = parser.parse_known_args()

        print("[STEP 1] Installing APK...")
        install_apk(args.device, args.apk)

        print("[STEP 1] Granting permissions...")
        grant_permissions(args.device, args.package, args.permissions)

        print("[STEP 1] Opening app...")
        launch_app(args.device, args.package, args.activity)

        options = UiAutomator2Options()
        options.platform_name = "Android"
        options.automation_name = "UiAutomator2"
        options.device_name = args.device or "Android"
        options.app_package = args.package
        options.app_activity = args.activity
        options.auto_grant_permissions = True
        options.no_reset = True

        cls.driver = webdriver.Remote(args.appium_url, options=options)
        cls.wait = WebDriverWait(cls.driver, 20)
        time.sleep(3)

    @classmethod
    def tearDownClass(cls) -> None:
        if getattr(cls, "driver", None):
            cls.driver.quit()

    # STEP 2: Sample test cases
    def test_app_launches_successfully(self) -> None:
        """Verify current package is the expected app package."""
        current_package = self.driver.current_package
        self.assertEqual(
            current_package,
            self.driver.capabilities.get("appPackage"),
            f"Unexpected package launched: {current_package}",
        )

    def test_home_screen_visible(self) -> None:
        """Check that a likely Flutter root view is visible."""
        # Use a generic XPath that often works for Flutter host view.
        try:
            self.wait.until(ec.presence_of_element_located((By.XPATH, "//*[contains(@class,'Flutter')]")))
            visible = True
        except TimeoutException:
            visible = False

        self.assertTrue(
            visible,
            "Could not find a Flutter view. Replace locator with your app-specific home screen locator.",
        )

    def test_click_example_button_if_present(self) -> None:
        """Try clicking a common button label and verify app stays responsive."""
        possible_labels = ["Login", "Sign in", "Continue", "Get Started"]
        clicked = False
        for label in possible_labels:
            elements = self.driver.find_elements(
                By.XPATH,
                f"//*[@text='{label}' or @content-desc='{label}']",
            )
            if elements:
                elements[0].click()
                clicked = True
                break

        self.assertTrue(
            clicked,
            "No sample button label found. Replace labels/locators with your app UI elements.",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
