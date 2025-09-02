# Deployment Guide - Nerds do Kart

## Option 1: Railway (Recommended)

1. Go to [railway.app](https://railway.app) and sign up
2. Click "Deploy from GitHub repo" 
3. Connect your GitHub account
4. Select your `nerds-do-kart` repository
5. Railway will auto-detect the Flask app and deploy it
6. Once deployed, go to Settings → Domains
7. Add custom domain: `nerdsdokart.com.br`

## Option 2: Heroku

1. Go to [heroku.com](https://heroku.com) and create account
2. Install Heroku CLI: `brew install heroku/brew/heroku`
3. Login: `heroku login`
4. Create app: `heroku create nerdsdokart`
5. Deploy: `git push heroku master`
6. Add domain: `heroku domains:add nerdsdokart.com.br`

## Option 3: Direct Upload to Railway

If GitHub continues to fail:
1. Create a ZIP file of your project (excluding .git folder)
2. Go to railway.app → New Project → Deploy from ZIP
3. Upload the ZIP file
4. Add domain in settings

## DNS Configuration

Once you have a hosting URL (like `nerdsdokart.railway.app`):

1. Go to registro.br DNS management
2. Add these DNS records:
   - Type: CNAME
   - Name: www
   - Value: [your-hosting-url]
   
   - Type: A
   - Name: @
   - Value: [hosting-ip-address]

Your app is production-ready with Gunicorn and all necessary files!