# 🧪 Laboratory Management System

A comprehensive Django-based laboratory management system for handling
veterinary pathology protocols, sample processing, and report generation.
This system provides a complete workflow for managing laboratory operations
from protocol submission to final report delivery.

## 🏥 System Overview

This laboratory management system is designed to streamline veterinary
pathology laboratory operations, providing:

- **Protocol Management**: Complete workflow for protocol submission, review,
  and approval
- **Sample Processing**: Track samples through reception, processing, and
  analysis stages
- **Report Generation**: Automated report creation with PDF generation and
  email delivery
- **User Management**: Role-based access control for veterinarians,
  histopathologists, and staff
- **Work Orders**: Comprehensive work order management and tracking
- **Email Notifications**: Automated email system for status updates and
  notifications

## 🛠 Technical Foundation

This system is built on top of a robust Django + Docker foundation that
provides:

- **Docker-based Development**: Complete containerized development environment
- **Modern Tech Stack**: PostgreSQL, Redis, Celery for background tasks
- **Frontend Assets**: esbuild + TailwindCSS for modern UI development
- **Code Quality**: Ruff for linting and formatting
- **Production Ready**: Gunicorn, WhiteNoise, and comprehensive configuration

### Built with Django 5.2.7 and Python 3.14.0

> **Note**: This project is based on the excellent
> [Docker Django Example](https://github.com/nickjj/docker-django-example) by
> [Nick Janetakis](https://nickjanetakis.com). The original template provides
> the Docker infrastructure, development workflow, and best practices that make
> this laboratory system possible.

## 🧾 Table of contents

- [Laboratory System Features](#laboratory-system-features)
- [Tech stack](#tech-stack)
- [Notable opinions and extensions](#notable-opinions-and-extensions)
- [Running this app](#running-this-app)
- [Files of interest](#files-of-interest)
  - [`.env`](#env)
  - [`run`](#run)
- [Running a script to automate renaming the project](#running-a-script-to-automate-renaming-the-project)
- [Updating dependencies](#updating-dependencies)
- [See a way to improve something?](#see-a-way-to-improve-something)
- [Additional resources](#additional-resources)
  - [Learn more about Docker and Django](#learn-more-about-docker-and-django)
  - [Deploy to production](#deploy-to-production)
- [About the author](#about-the-author)

## 🧪 Laboratory System Features

### Core Functionality

#### 🔐 Authentication & Authorization

- Email verification system for veterinarians
- Role-based access control (Veterinarian, Histopathologist, Staff)
- Secure password reset functionality
- Session management and audit logging

#### 📋 Protocol Management

- Protocol submission and review workflow
- Support for Cytology and Histopathology analysis types
- Protocol editing and status tracking
- Automatic protocol numbering system

#### 🧬 Sample Processing

- Sample reception and registration
- Cassette and slide management
  - Sample tracking through processing stages
  - Visual slide registration interface with Vue.js

#### 📊 Report Generation

- Automated PDF report generation using ReportLab
- Report templates for different analysis types
- Report finalization and approval workflow
- Email delivery of completed reports

#### 📦 Work Order Management

- Work order creation and tracking
- Service management and pricing
- Work order status updates
- PDF work order generation

#### 📧 Email System

- Automated email notifications
- Email verification for new users
- Report delivery via email
- Configurable email templates

### Advanced Features

#### 📈 Dashboard & Analytics

- User-specific dashboards
- Protocol and report statistics
- System performance metrics
  - Data visualization

#### 🔍 Search & Filtering

- Advanced search capabilities
- Filter protocols by status, type, and date
- Quick access to recent activities
- Export functionality

#### 🛡️ Security Features

- CSRF protection
- XSS prevention
- SQL injection protection
- Secure file handling
- Permission-based access control

#### 📱 Modern UI/UX

- Responsive design with TailwindCSS
- Interactive components with Vue.js
- Real-time notifications
- Intuitive navigation

## 🧬 Tech Stack

### Back-end

- [PostgreSQL](https://www.postgresql.org/) - Primary database
- [Redis](https://redis.io/) - Caching and session storage
- [Celery](https://github.com/celery/celery) - Background task processing
- [ReportLab](https://www.reportlab.com/) - PDF generation for reports and work
  orders
- [qrcode](https://github.com/lincolnloop/python-qrcode) - QR code generation for samples
- [Django](https://www.djangoproject.com/) - Web framework
- [Gunicorn](https://gunicorn.org/) - WSGI HTTP server
- [WhiteNoise](https://github.com/evansd/whitenoise) - Static file serving

### Front-end

- [esbuild](https://esbuild.github.io/) - JavaScript bundler
- [TailwindCSS](https://tailwindcss.com/) - CSS framework
- [Heroicons](https://heroicons.com/) - Icon library
- [Vue.js 3](https://vuejs.org/) - Interactive UI components
- [Alpine.js](https://alpinejs.dev/) - Lightweight JavaScript framework

## 🍣 Notable opinions and extensions

Django is an opinionated framework and I've added a few extra opinions based on
having Dockerized and deployed a number of Django projects. Here's a few (but
not all) note worthy additions and changes.

- **Packages and extensions**:
  - *[gunicorn](https://gunicorn.org/)* for an app server in both development and
  production
  - *[whitenoise](https://github.com/evansd/whitenoise)* for serving static files
  - *[django-debug-toolbar](https://github.com/jazzband/django-debug-toolbar)* for
    displaying info about a request
- **Linting and formatting**:
  - *[ruff](https://github.com/astral-sh/ruff)* is used to lint and format the code base
- **Django apps**:
  - Add `pages` app to render a home page
  - Add `up` app to provide a few health check pages
- **Config**:
  - Log to STDOUT so that Docker can consume and deal with log output
  - Extract a bunch of configuration settings into environment variables
  - Rename project directory from its custom name to `config/`
  - `src/config/settings.py` and the `.env` file handles configuration in all environments
- **Front-end assets**:
  - `assets/` contains all your CSS, JS, images, fonts, etc. and is managed by esbuild
  - Custom `502.html` and `maintenance.html` pages
  - Generate favicons using modern best practices
- **Django defaults that are changed**:
  - Use Redis as the default Cache back-end
  - Use signed cookies as the session back-end
  - `public/` is the static directory where Django will serve static files from
  - `public_collected/` is where `collectstatic` will write its files to

Besides the Django app itself:

- [uv](https://github.com/astral-sh/uv) is used for package management instead of
  `pip3` (builds on my machine are ~10x faster!)
- Docker support has been added which would be any files having `*docker*` in
  its name
- GitHub Actions have been set up

## 🚀 Running the Laboratory System

### Prerequisites

You'll need to have [Docker installed](https://docs.docker.com/get-docker/).
It's available on Windows, macOS and most distros of Linux. If you're new to
Docker and want to learn it in detail check out the [additional resources
links](#learn-more-about-docker-and-django) near the bottom of this README.

You'll also need to enable Docker Compose v2 support if you're using Docker
Desktop. On native Linux without Docker Desktop you can [install it as a plugin
to Docker](https://docs.docker.com/compose/install/linux/). It's been generally
available for a while now and is stable. This project uses specific [Docker
Compose v2
features](https://nickjanetakis.com/blog/optional-depends-on-with-docker-compose-v2-20-2)
that only work with Docker Compose v2 2.20.2+.

If you're using Windows, it will be expected that you're following along inside
of [WSL or WSL
2](https://nickjanetakis.com/blog/a-linux-dev-environment-on-windows-with-wsl-2-docker-desktop-and-more).
That's because we're going to be running shell commands. You can always modify
these commands for PowerShell if you want.

### Quick Start

#### Clone this repository:

```sh
git clone <your-repository-url> laboratory-system
cd laboratory-system
```

#### Copy an example .env file because the real one is git ignored:

```sh
cp .env.example .env
```

#### Build everything:

*The first time you run this it's going to take 5-10 minutes depending on your
internet connection speed and computer's hardware specs. That's because it's
going to download a few Docker images and build the Python + Yarn dependencies.*

```sh
docker compose up --build
```

Now that everything is built and running we can treat it like any other Django
app.

Did you receive a `depends_on` "Additional property required is not allowed"
error? Please update to at least Docker Compose v2.20.2+ or Docker Desktop
4.22.0+.

Did you receive an error about a port being in use? Chances are it's because
something on your machine is already running on port 8000. Check out the docs
in the `.env` file for the `DOCKER_WEB_PORT_FORWARD` variable to fix this.

Did you receive a permission denied error? Chances are you're running native
Linux and your `uid:gid` aren't `1000:1000` (you can verify this by running
`id`). Check out the docs in the `.env` file to customize the `UID` and `GID`
variables to fix this.

#### Setup the initial database:

```sh
# You can run this from a 2nd terminal.
./run manage migrate
```

*We'll go over that `./run` script in a bit!*

#### Check it out in a browser:

Visit <http://localhost:8000> in your favorite browser.

The laboratory system will be available with the following default access:

- **Home Page**: <http://localhost:8000> - System overview and navigation
- **Admin Interface**: <http://localhost:8000/admin> - Django admin for system management
- **User Registration**: <http://localhost:8000/accounts/register> - Create new user accounts
- **Login**: <http://localhost:8000/accounts/login> - User authentication

> **Note**: Check the `TEST_CREDENTIALS.md` file for test user credentials and the `LABORATORY_SETUP.md` file for detailed setup instructions.

#### Linting the code base:

```sh
# You should get no output (that means everything is operational).
./run lint
```

#### Formatting the code base:

```sh
# You should see that everything is unchanged (it's all already formatted).
./run format
```

*There's also a `./run quality` command to run the above commands together.*

#### Running the test suite:

```sh
# You should see all passing tests. Warnings are typically ok.
./run manage test
```

#### Stopping everything:

```sh
# Stop the containers and remove a few Docker related resources associated to this project.
docker compose down
```

You can start things up again with `docker compose up` and unlike the first
time it should only take seconds.

## 🔍 Files of interest

I recommend checking out most files and searching the code base for `TODO:`,
but please review the `.env` and `run` files before diving into the rest of the
code and customizing it. Also, you should hold off on changing anything until
we cover how to customize this example app's name with an automated script
(coming up next in the docs).

### `.env`

This file is ignored from version control so it will never be commit. There's a
number of environment variables defined here that control certain options and
behavior of the application. Everything is documented there.

Feel free to add new variables as needed. This is where you should put all of
your secrets as well as configuration that might change depending on your
environment (specific dev boxes, CI, production, etc.).

### `run`

You can run `./run` to get a list of commands and each command has
documentation in the `run` file itself.

It's a shell script that has a number of functions defined to help you interact
with this project. It's basically a `Makefile` except with [less
limitations](https://nickjanetakis.com/blog/replacing-make-with-a-shell-script-for-running-your-projects-tasks).
For example as a shell script it allows us to pass any arguments to another
program.

This comes in handy to run various Docker commands because sometimes these
commands can be a bit long to type. Feel free to add as many convenience
functions as you want. This file's purpose is to make your experience better!

*If you get tired of typing `./run` you can always create a shell alias with
`alias run=./run` in your `~/.bash_aliases` or equivalent file. Then you'll be
able to run `run` instead of `./run`.*

#### Start and setup the project:

This won't take as long as before because Docker can re-use most things. We'll
also need to setup our database since a new one will be created for us by
Docker.

```sh
docker compose up --build

# Then in a 2nd terminal once it's up and ready.
./run manage migrate
```

#### Sanity check to make sure the tests still pass:

It's always a good idea to make sure things are in a working state before
adding custom changes.

```sh
# You can run this from the same terminal as before.
./run quality
./run manage test
```

If everything passes now you can optionally `git add -A && git commit -m
"Initial commit"` and start customizing your app. Alternatively you can wait
until you develop more of your app before committing anything. It's up to you!

#### Tying up a few loose ends:

You'll probably want to create a fresh `CHANGELOG.md` file for your project. I
like following the style guide at <https://keepachangelog.com/> but feel free
to use whichever style you prefer.

Since this project is MIT licensed you should keep my name and email address in
the `LICENSE` file to adhere to that license's agreement, but you can also add
your name and email on a new line.

If you happen to base your app off this example app or write about any of the
code in this project it would be rad if you could credit this repo by linking
to it. If you want to reference me directly please link to my site at
<https://nickjanetakis.com>. You don't have to do this, but it would be very
much appreciated!

## 🛠 Updating dependencies

You can run `./run uv:outdated` or `./run yarn:outdated` to get a list of
outdated dependencies based on what you currently have installed. Once you've
figured out what you want to update, go make those updates in your
`pyproject.toml` and / or `package.json` file.

Or, let's say you've customized your app and it's time to add a new dependency,
either for Python or Node.

### In development

#### Option 1

1. Directly edit `pyproject.toml` or `assets/package.json` to add your package
2. `./run deps:install` or `./run deps:install --no-build`
   - The `--no-build` option will only write out a new lock file without re-building your image

#### Option 2

1. Run `./run uv add mypackage --no-sync` or `run yarn add mypackage --no-lockfile` which will update your `pyproject.toml` or `assets/package.json` with the latest version of that package but not install it
2. The same step as step 2 from option 1

Either option is fine, it's up to you based on what's more convenient at the
time. You can modify the above workflows for updating an existing package or
removing one as well.

You can also access `uv` and `yarn` in Docker with `./run uv` and `./run yarn`
after you've upped the project.

### In CI

You'll want to run `docker compose build` since it will use any existing lock
files if they exist. You can also check out the complete CI test pipeline in
the [run](https://github.com/nickjj/docker-django-example/blob/main/run) file
under the `ci:test` function.

### In production

This is usually a non-issue since you'll be pulling down pre-built images from
a Docker registry but if you decide to build your Docker images directly on
your server you could run `docker compose build` as part of your deploy
pipeline which is similar to how it would work in CI.

## 🤝 See a way to improve something?

If you see anything that could be improved please open an issue or start a PR.
Any help is much appreciated!

## 🌎 Additional resources

Now that you have your app ready to go, it's time to build something cool! If
you want to learn more about Docker, Django and deploying a Django app here's a
couple of free and paid resources. There's Google too!

### Learn more about Docker and Django

#### Official documentation

- <https://docs.docker.com/>
- <https://docs.djangoproject.com/en/5.2/>

#### Courses / books

- [https://diveintodocker.com](https://diveintodocker.com?ref=docker-django-example)
  is a course I created which goes over the Docker and Docker Compose
  fundamentals
- William Vincent has a bunch of [beginner and advanced Django
  books](https://gumroad.com/a/139727987). He also co-hosts the [Django
  Chat](https://djangochat.com/) podcast

### Deploy to production

I'm creating an in-depth course related to deploying Dockerized web apps. If
you want to get notified when it launches with a discount and potentially get
free videos while the course is being developed then [sign up here to get
notified](https://nickjanetakis.com/courses/deploy-to-production).

## 👀 About the authors

### Laboratory System Developer

This laboratory management system was developed to provide a comprehensive solution for veterinary pathology laboratories. The system implements modern web development practices and provides a complete workflow for managing laboratory operations.

### Original Django Template Author

- **Nick Janetakis** | <https://nickjanetakis.com> | [@nickjanetakis](https://twitter.com/nickjanetakis)

Nick is a self taught developer and has been freelancing for the last ~20 years.
You can read about everything he's learned along the way on his site at
[https://nickjanetakis.com](https://nickjanetakis.com/).

There's hundreds of [blog posts](https://nickjanetakis.com/) and a couple
of [video courses](https://nickjanetakis.com/courses) on web development and
deployment topics. He also has a [podcast](https://runninginproduction.com)
where he talks with folks about running web apps in production.

### Acknowledgments

This laboratory system is built on top of Nick's excellent [Docker Django Example](https://github.com/nickjj/docker-django-example) template, which provides the solid foundation of Docker infrastructure, development workflow, and best practices that make this system possible. The original template demonstrates modern Django development practices and production-ready deployment strategies.
