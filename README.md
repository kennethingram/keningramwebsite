# keningramwebsite

Personal website for Ken Ingram — [www.keningram.ca](https://www.keningram.ca)

A clean, elegant static site inspired by mirandakerr.com, featuring professional and music content.

## Stack

Pure HTML, CSS, and vanilla JavaScript — no build tools required.

## Setup: Publishing on GitHub Pages

### 1. Create the repository

Go to [github.com/new](https://github.com/new) and create a public repository named **`keningramwebsite`** under your account (`kennethingram`).

### 2. Push this code

```bash
git init
git add .
git commit -m "Initial commit: personal website"
git branch -M main
git remote add origin https://github.com/kennethingram/keningramwebsite.git
git push -u origin main
```

### 3. Enable GitHub Pages

1. Go to **Settings → Pages** in the repository.
2. Under **Source**, choose **GitHub Actions**.
3. The included `.github/workflows/deploy.yml` will automatically deploy on every push to `main`.

### 4. Configure custom domain (www.keningram.ca)

The `CNAME` file in the repo root is already set to `www.keningram.ca`.

Add the following DNS records at your domain registrar:

| Type  | Name | Value                      |
|-------|------|----------------------------|
| CNAME | www  | kennethingram.github.io    |

Or, to also support the apex domain (`keningram.ca`), add all four GitHub Pages A records:

| Type | Name | Value          |
|------|------|----------------|
| A    | @    | 185.199.108.153 |
| A    | @    | 185.199.109.153 |
| A    | @    | 185.199.110.153 |
| A    | @    | 185.199.111.153 |

DNS changes can take up to 48 hours to propagate. GitHub will automatically provision an HTTPS certificate via Let's Encrypt once DNS is confirmed.

## Structure

```
keningramwebsite/
├── index.html              # Main page
├── CNAME                   # Custom domain
├── css/
│   └── style.css           # All styles
├── js/
│   └── main.js             # Interactivity
├── img/
│   └── favicon.svg         # Site favicon
└── .github/
    └── workflows/
        └── deploy.yml      # Auto-deploy to GitHub Pages
```

## Adding a Photo

Replace the placeholder portrait in the About section by adding your photo to `img/` and updating the `about-portrait` element in `index.html`:

```html
<img src="img/ken-ingram.jpg" alt="Ken Ingram" class="about-portrait-photo" />
```

Then add to `css/style.css`:

```css
.about-portrait-photo {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
```
