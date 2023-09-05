
import browser_cookie3
from rich.console import Console


class CookieFetcher:
    def try_append_aula_cookies(self, aula_cookies, browser_name):
        result = ''
        try:
            cookies = self.get_cookies_from_browser(browser_name)
            if (cookies):
                aula_cookies.append(cookies)
                result = 'found'
            else:
                result = 'notFound'
        except browser_cookie3.BrowserCookieError:
            result = 'notFound'
        except:
            result = 'error'

        if result == 'notFound':
            message = "[yellow]not found[/]"
        elif result == 'found':
            message = "[green]found[/]"
        elif result == 'error':
            message = "[red]error occured[/]"
        else:
            message = "[red]unknown error occured[/]"

        console = Console()
        console.print(f"{browser_name} cookies: {message}")

    def get_cookies_from_browser(self, browser_name):
        domain = 'aula.dk'
        if browser_name == 'Chrome':
            return browser_cookie3.chrome(domain_name=domain)
        elif browser_name == 'Chromium':
            return browser_cookie3.chromium(domain_name=domain)
        elif browser_name == 'Opera':
            return browser_cookie3.opera(domain_name=domain)
        elif browser_name == 'Opera GX':
            return browser_cookie3.opera_gx(domain_name=domain)
        elif browser_name == 'Brave':
            return browser_cookie3.brave(domain_name=domain)
        elif browser_name == 'Edge':
            return browser_cookie3.edge(domain_name=domain)
        elif browser_name == 'Vivaldi':
            return browser_cookie3.vivaldi(domain_name=domain)
        elif browser_name == 'Firefox':
            return browser_cookie3.firefox(domain_name=domain)
        elif browser_name == 'Safari':
            return browser_cookie3.safari(domain_name=domain)

    def get_aula_cookies(self):
        aula_cookies = []
        self.try_append_aula_cookies(aula_cookies, 'Chrome')
        self.try_append_aula_cookies(aula_cookies, 'Chromium')
        self.try_append_aula_cookies(aula_cookies, 'Opera')
        self.try_append_aula_cookies(aula_cookies, 'Opera GX')
        self.try_append_aula_cookies(aula_cookies, 'Brave')
        self.try_append_aula_cookies(aula_cookies, 'Edge')
        self.try_append_aula_cookies(aula_cookies, 'Vivaldi')
        self.try_append_aula_cookies(aula_cookies, 'Firefox')
        self.try_append_aula_cookies(aula_cookies, 'Safari')
        return aula_cookies
