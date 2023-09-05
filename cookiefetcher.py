
import browser_cookie3
from rich.console import Console


class CookieFetcher:
    def tryAppendAulaCookies(self, aulaCookies, browserName):
        result = ''
        try:
            cookies = self.getCookiesFromBrowser(browserName)
            if (cookies):
                aulaCookies.append(cookies)
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
        console.print(f"{browserName} cookies: {message}")

    def getCookiesFromBrowser(self, browserName):
        domain = 'aula.dk'
        if browserName == 'Chrome':
            return browser_cookie3.chrome(domain_name=domain)
        elif browserName == 'Chromium':
            return browser_cookie3.chromium(domain_name=domain)
        elif browserName == 'Opera':
            return browser_cookie3.opera(domain_name=domain)
        elif browserName == 'Opera GX':
            return browser_cookie3.opera_gx(domain_name=domain)
        elif browserName == 'Brave':
            return browser_cookie3.brave(domain_name=domain)
        elif browserName == 'Edge':
            return browser_cookie3.edge(domain_name=domain)
        elif browserName == 'Vivaldi':
            return browser_cookie3.vivaldi(domain_name=domain)
        elif browserName == 'Firefox':
            return browser_cookie3.firefox(domain_name=domain)
        elif browserName == 'Safari':
            return browser_cookie3.safari(domain_name=domain)

    def getAulaCookies(self):
        aulaCookies = []
        self.tryAppendAulaCookies(aulaCookies, 'Chrome')
        self.tryAppendAulaCookies(aulaCookies, 'Chromium')
        self.tryAppendAulaCookies(aulaCookies, 'Opera')
        self.tryAppendAulaCookies(aulaCookies, 'Opera GX')
        self.tryAppendAulaCookies(aulaCookies, 'Brave')
        self.tryAppendAulaCookies(aulaCookies, 'Edge')
        self.tryAppendAulaCookies(aulaCookies, 'Vivaldi')
        self.tryAppendAulaCookies(aulaCookies, 'Firefox')
        self.tryAppendAulaCookies(aulaCookies, 'Safari')
        return aulaCookies
