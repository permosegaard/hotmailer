# Hotmailer

An automated reputation builder for Hotmail's anti-spam system using simulated agents.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Configuration](#configuration)
- [TODO](#todo)
- [FAQ / Troubleshooting](#faq)
- [Contributing](#contributing)
- [Rationale](#rationale)
- [License](#license)

<a name="installation"></a>
## Installation

 * There's a Vagrantfile in the repo that should be good to go given some monior tweaking
 
 * For a manual install, a standard 15.10 install with pip3 installs of nltk (and wordnet dataset) and faker should get you running, see files/provision.sh if you're unsure

<a name="usage"></a>
## Usage

 * It's a python3 script with a main method that takes a list of local accounts and hotmail accounts as respective arguments with form "address:password|address:password|..."
 
 * You may find it easier to put a simple shell script together using the code below as a base ...

```bash
#!/bin/bash

LOCAL_ACCOUNTS=(
	"test1@domain.tld:password1"
	"test2@domain.tld:password2"
	"test3@domain.tld:password3"
)

HOTMAIL_ACCOUNTS=(
	"test1@hotmail.com:password1"
	"test2@hotmail.com:password2"
	"test3@hotmail.com:password3"
)

./hotmailer.py "$( IFS='|'; echo "${LOCAL_ACCOUNTS[*]}" )" "$( IFS='|'; echo "${HOTMAIL_ACCOUNTS[*]}" )"
```

<a name="features"></a>
## Features

* Multiprocess which will scale as high as your hardware, specifically no major GIL contraints.

* Agent based that simulate real email users with tunable random delays to work around the machine learning system employed by hotmail.

* Content randomisation to prevent classification by hotmail's machine learning algorithms.

  * Body content generation based on supplied data, which is then tumbeled for synonyms.
  
  * Body formatting and structure randomisation.
  
  * Appropriate subject generation and randomisation.

* Tuning based on simple variables for agressiveness, randomisation and content generation.

* Engineered to be easy to read, reason about and extended as part of a more complex system.

* Safe guards to ensure hotmails sender limits aren't exceeded.

* Outputs basic sending chain information for progress tracking.

<a name="configuration"></a>
## Configuration

* Various variables are avaiable at the top of the code, everything should be named self-documenting.
  Feel free to open an issue for any that need clarfication

<a name="todo"></a>
## TODO

* [ ] buildout support for accounts with a non-email imap username
* [ ] outlook accounts as well as standard hotmail accounts
* [ ] more variety in content randomisation
* [ ] fixed (randomly generated) names for accounts

<a name="faq"></a>
## FAQ / Troubleshooting

* Should I list domains in safe senders?
  * blah.

* How many accounts should I use?
  * blah.

* How should I setup the tuning parameters?
  * blah.

* How quickly can I expect to see results?
  * blah.

<a name="contibuting"></a>
## Contributing

Best ways to contribute
* Star it on GitHub - staring the repo means i'll be more likely to spend time developing this project
* [Promote](#promotion)
* Open [issues/tickets](https://github.com/permosegaard/hotmailer/issues)
* Submit fixes and/or improvements with [Pull Requests](#source-code)

### Promotion

Like the project? Please support to ensure continued development going forward:
* Star this repo on [GitHub][hotmailer]
* Follow the repo on [GitHub][hotmailer]
* Follow me
  * [GitHub](https://github.com/permosegaard)

### Source code

Contributions and pull requests are welcome.

No real formal process is in place yet, standard github conventions welcome

<a name="rationale"></a>
## Rationale

Spin up a new mail server with a new domain, you'll quickly find that most of the major providers don't have an issue with this until you get to testing deliverability with hotmail.
You would think that contacting Hotmail's Postmaster (per the docs) would provide some assistance but you're likely to get the dreaded "we are unable to assist at this time" response.
Officialy adivce says that given enough volume your deliverability will likely resolve itself within a couple of weeks, but ain't nobody got time for that!

<a name="license"></a>
## License

See [LICENSE](LICENSE)

<!---
Link References
-->

[hotmailer-repo]:https://github.com/permosegaard/hotmailer
