# GlycoLens 
### *Vision-Based Nutritional Intelligence & Insulin Bolus Estimator*

**GlycoLens** is a clinical utility tool designed to help Type 1 Diabetics estimate carbohydrate counts and insulin doses using computer vision. By analyzing a photo of a meal, the system identifies food items, estimates portions, and suggests an insulin dose based on the user's personal biometrics and current blood glucose levels.

---

##  Key Features

* **Computer Vision Analysis:** Powered by YOLOv8 for real-time food detection.
* **Nutritional Mapping:** Integrated with the FatSecret REST API for accurate carb and Glycemic Index (GI) data.
* **Dual-Unit Bolus Engine:** Supports both **mg/dL** and **mmol/L** for global compatibility.
* **Glycemic Load Assessment:** Color-coded risk tags (Low, Moderate, High) based on the impact on blood sugar.
* **Privacy First:** All meal history and biometric settings are stored locally in the browser via `LocalStorage`.
* **Glassmorphism UI:** A clean, modern, and clinical interface designed for ease of use.

---

##  System Architecture

The system follows a decoupled Client-Server model to ensure high-performance inference while maintaining a lightweight frontend.

1.  **Image Capture:** User uploads a photo via the web interface.
2.  **Detection:** The YOLOv8m model identifies object classes and calculates bounding box area ratios.
3.  **Filtering:** A "Class-Validation Gate" filters out non-food objects (e.g., tables, cutlery).
4.  **Nutrition Query:** The backend maps YOLO labels to the FatSecret API to retrieve carbohydrate and GI data.
5.  **Bolus Calculation:** The system combines nutritional data with user-provided insulin ratios to suggest a dose.

---

##  Getting Started

### 1. Prerequisites
* Python 3.9+
* A FatSecret Developer Account (for API keys)
* VS Code (recommended)

### 2. Installation
Clone the repository and install the required dependencies:
```bash
pip install fastapi uvicorn ultralytics python-dotenv requests pillow
```
### 3. Configuration
Create a `.env` file in the root directory and add your FatSecret credentials:

```plaintext
FATSECRET_CLIENT_ID=your_id_here
FATSECRET_CLIENT_SECRET=your_secret_here
```
### 4. Running the App

**Start the Backend:**
Open your terminal and run:
```bash
python main.py
```
### Launch the Frontend
Open `index.html` using the **Live Server** extension in VS Code or simply double-click the file to open it in your browser.

---

###  Built With
* **Backend:** [FastAPI](https://fastapi.tiangolo.com/) - High-performance Python web framework.
* **Vision:** [YOLOv8](https://ultralytics.com/yolov8) - State-of-the-art object detection.
* **Nutrition Data:** [FatSecret Platform API](https://platform.fatsecret.com/) - Comprehensive food database.
* **Frontend:** Vanilla JavaScript, HTML5, and CSS3.

---

###  Medical Disclaimer ###
**GlycoLens is a proof-of-concept utility.** The calculations provided are estimates based on visual data. Users should never dose insulin based solely on this app's output. Always verify with a blood glucose meter and consult a medical professional. GlycoLens is not a replacement for clinical advice or professional medical devices.