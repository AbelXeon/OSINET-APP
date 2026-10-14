# ⚡ OSINT // CONSOLE (PWA)

> A lightweight, Neo-Brutalist Open-Source Intelligence (OSINT) and reconnaissance Progressive Web App (PWA), optimized for serverless deployment on Vercel.

---

## 📌 Overview

**OSINT // CONSOLE** transforms multi-vector intelligence workflows into a fast, mobile-first web application. Featuring a high-contrast Neo-Brutalist interface, it provides access to public intelligence related to network infrastructure, digital identities, domains, and multimedia metadata.

The application is designed for serverless environments, with a focus on efficient request handling and bounded execution times to help minimize timeout failures on platforms such as Vercel.

---

## 🛠️ Features & Supported Modules

| Tool | Icon | Description | Core Capabilities |
|:---|:---:|:---|:---|
| **IP Intel** | 📡 | Network and geolocation lookup | IP geolocation, ISP, ASN, reverse DNS, open-port information, and CVE-related data via Shodan InternetDB |
| **Domain Recon** | 🌐 | DNS and mail infrastructure analysis | DNS records (A, MX, NS, TXT), SPF/DMARC presence, WHOIS references, and archive links |
| **Phone Lookup** | 📱 | Telephone number parsing and routing | E.164 formatting, carrier identification where available, region detection, and quick WhatsApp/Telegram links |
| **Telegram** | ✈️ | Public profile intelligence | Public `@username` lookups, available profile information, and entity classification (bot, user, or channel) |
| **Email Scan** | 📧 | Email verification and digital footprint | Mail exchange validation, Gravatar profile detection, and breach-related cross-referencing |
| **Breach Check** | 💥 | Compromised account checks | Queries the XposedOrNot breach-checking service for reported data breach exposures |
| **Name Search** | 🧑 | Username permutations and targeted searches | Algorithmic username permutation generation and automated social media and corporate search queries |
| **Dork Builder** | 🕵️ | Search query automation | Targeted reconnaissance queries for public paste sites, GitHub exposures, and publicly accessible documents |
| **Image EXIF** | 📷 | Image metadata and geolocation extraction | Camera model, software, timestamps, lens information, GPS coordinates, Google Maps links, and reverse image search links |

> **Note:** Results depend on the capabilities, availability, rate limits, and data coverage of the external services used by each module. Not every lookup can return complete or verified information.

---

## 📂 Project Structure

```text
OSIAPP/
├── .well-known/
│   └── assetlinks.json       # Android Digital Asset Links for TWA integration
├── generate_icons.py         # Icon asset generation utility
├── icon-192.png              # Standard PWA icon (192 × 192)
├── icon-512.png              # Large PWA icon (512 × 512)
├── index.html                # Single-page UI and reconnaissance console
├── manifest.json             # Web App Manifest configuration
├── maskable-512.png          # Android adaptive/maskable icon
├── pyproject.toml            # Python project and runtime configuration
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies
├── scan.py                   # Python backend and scan request handlers
└── sw.js                     # Service Worker for offline asset caching
```

---

## 🚀 Getting Started

### 1. Prerequisites

Before running the application, make sure you have the following:

- Python 3.10 or later
- `pip` for installing Python dependencies
- Git for cloning the repository
- A modern browser, such as Chrome, Brave, Safari, Edge, or Firefox
- Node.js and npm if you plan to use the Vercel CLI

### 2. Clone the Repository

Clone your repository and navigate to the project directory:

```bash
git clone <your-repo-url>
cd OSIAPP
```

Replace `<your-repo-url>` with the actual URL of your Git repository.

### 3. Create a Virtual Environment

A virtual environment keeps the project's Python dependencies isolated from other Python installations.

**Linux / macOS**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows — Command Prompt**

```bat
python -m venv venv
venv\Scripts\activate
```

**Windows — PowerShell**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 5. Run the Frontend Locally

To preview the static frontend, start Python's built-in HTTP server:

```bash
python -m http.server 8000
```

Open the following address in your browser:

```text
http://localhost:8000
```

**Important:** Python's built-in HTTP server serves static files only. It does not execute `scan.py` as a backend API. To test the scanning features locally, you must also run the backend through an appropriate local development setup that routes `/api/scan` requests to the Python handler.

---

## ☁️ Deployment on Vercel

The project includes a Python backend intended for serverless deployment. Successful deployment depends on the Vercel configuration, runtime entry point, routing rules, and dependencies.

### Option A: Deploy Using the Vercel CLI

Install the Vercel CLI:

```bash
npm install -g vercel
```

Navigate to the project directory and start deployment:

```bash
cd OSIAPP
vercel
```

Follow the prompts to link the project to your Vercel account.

For a production deployment, use:

```bash
vercel --prod
```

### Option B: Deploy Through Git Integration

1. Push the project to GitHub, GitLab, or another supported Git provider.
2. Open the [Vercel Dashboard](https://vercel.com/dashboard).
3. Select **Add New Project**.
4. Import the repository containing the application.
5. Review the build and deployment settings.
6. Ensure the Python backend entry point and `/api/scan` routing are configured correctly.
7. Deploy the project.

### Deployment Notes

- Ensure `requirements.txt` contains all required Python dependencies.
- Verify that `pyproject.toml` and any Vercel routing configuration match the actual backend entry point.
- Confirm that the deployed backend exposes the `/api/scan` endpoint.
- Configure API keys or other secrets through Vercel's environment variable settings if required by your implementation.
- Do not commit API keys, passwords, or other secrets to the repository.
- Test each module after deployment to confirm that external services and backend routes work correctly.

> **Compatibility warning:** A `pyproject.toml` file alone does not guarantee that Vercel will discover and route a Python HTTP handler correctly. Confirm that your actual deployment configuration supports the structure used by `scan.py`.

---

## 📱 Installing as a PWA / Mobile App

OSINT // CONSOLE includes Progressive Web App (PWA) assets intended to support installation as a standalone application on compatible devices.

### Android — Chrome / Brave

1. Open the deployed application in your browser.
2. Open the browser menu.
3. Select **Install app** or **Add to Home screen**, depending on the browser.

### iOS — Safari

1. Open the deployed application in Safari.
2. Tap the **Share** button.
3. Scroll through the available actions.
4. Select **Add to Home Screen**.

### Desktop — Chrome / Edge

1. Open the deployed application.
2. Look for the installation icon in the address bar or browser menu.
3. Select the option to install the application.

### PWA Requirements

For installation and offline functionality to work as intended:

- Serve the application over HTTPS, except when using supported local development origins.
- Ensure `manifest.json` is valid and correctly linked from `index.html`.
- Verify that the referenced icons exist and have the expected dimensions.
- Register `sw.js` correctly from the frontend.
- Confirm that the Service Worker caches the intended static assets.
- Test the installation flow in each target browser.

**Android Trusted Web Activity (TWA):** If you package the PWA as an Android application using a TWA, verify that `.well-known/assetlinks.json` contains the correct Android package name and signing-certificate fingerprint.

---

## 📡 API Reference

The backend is designed to handle reconnaissance requests through the `/api/scan` endpoint.

### 1. Standard Reconnaissance — GET

**Endpoint**

```http
GET /api/scan?tool={tool_name}&target={target_query}
```

**Query Parameters**

| Parameter | Required | Description |
|:---|:---:|:---|
| `tool` | Yes | The reconnaissance module to execute |
| `target` | Yes | The IP address, domain, phone number, username, email address, or other supported search target |

**Supported Tool Identifiers**

| Tool Identifier | Module |
|:---|:---|
| `ip` | IP Intel |
| `domain` | Domain Recon |
| `phone` | Phone Lookup |
| `tg` | Telegram |
| `email` | Email Scan |
| `breach` | Breach Check |
| `name` | Name Search |
| `dork` | Dork Builder |

**Example Request**

```http
GET /api/scan?tool=ip&target=8.8.8.8
```

Another example:

```http
GET /api/scan?tool=domain&target=example.com
```

For a phone number, use URL encoding where necessary:

```text
/api/scan?tool=phone&target=%2B251911234567
```

The exact response structure, error format, and supported parameters depend on the implementation in `scan.py`.

### 2. Image EXIF and Metadata Extraction — POST

Image metadata extraction uses a POST request with a JSON payload.

**Endpoint**

```http
POST /api/scan
Content-Type: application/json
```

**Example Request Body**

```json
{
  "tool": "image",
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQ..."
}
```

The `image` field should contain an image data URL with a Base64-encoded image.

**Example using JavaScript**

```javascript
async function scanImage(imageDataUrl) {
  const response = await fetch("/api/scan", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      tool: "image",
      image: imageDataUrl
    })
  });

  if (!response.ok) {
    throw new Error(`Image scan failed: HTTP ${response.status}`);
  }

  return await response.json();
}
```

Pass a valid image data URL to `scanImage()`. The backend must support the `image` tool and the request format shown above for this example to work.

> **Privacy note:** EXIF metadata may contain sensitive information, including GPS coordinates and timestamps. Review image metadata carefully before sharing it publicly.

---

## 🔒 Security, Privacy & Responsible Use

OSINT // CONSOLE is intended for lawful, responsible, and ethical intelligence gathering.

Use the application for purposes such as:

- Authorized security assessments
- Defensive reconnaissance
- Educational research
- Security awareness and investigation
- Reviewing your own digital footprint
- Analyzing publicly available information

### Important Considerations

- **Authorization:** Only conduct security testing against systems you own or have explicit permission to assess.
- **Privacy:** Publicly accessible information can still be personal or sensitive. Handle collected information responsibly.
- **Data accuracy:** External intelligence services may return incomplete, outdated, or incorrect results. Independently verify important findings.
- **API security:** Protect API keys and credentials. Avoid exposing privileged secrets in frontend code or public repositories.
- **Rate limits:** Respect the usage policies and rate limits of external services.
- **Legal compliance:** Follow all applicable local and international laws concerning privacy, data protection, and unauthorized computer access.

---

## ⚖️ Legal Disclaimer

OSINT // CONSOLE accesses information through external services, publicly available records, search engines, and image metadata, depending on the selected module.

The application is provided for authorized security auditing, defensive intelligence gathering, educational research, and personal digital-footprint reviews.

The developer assumes no responsibility for misuse of the application. Users are responsible for ensuring that their activities comply with applicable laws, third-party service terms, and privacy requirements.

**Use this tool responsibly. Access only information and systems you are legally permitted to access.**

---

## 📄 License

No license has been specified in this repository documentation.

If you intend to distribute or allow others to reuse this project, add an appropriate `LICENSE` file and update this section to identify the chosen license.
