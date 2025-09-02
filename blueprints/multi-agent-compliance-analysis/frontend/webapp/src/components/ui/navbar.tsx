// MIT No Attribution
//
// Copyright 2025 Amazon Web Services
//
// Permission is hereby granted, free of charge, to any person obtaining a copy of this
// software and associated documentation files (the "Software"), to deal in the Software
// without restriction, including without limitation the rights to use, copy, modify,
// merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
// permit persons to whom the Software is furnished to do so.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
// INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
// PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
// HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
// OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
// SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import { useState } from "react";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuItem,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuPortal,
  DropdownMenuSubContent,
} from "@/components/ui/dropdown-menu";
import {
  Drawer,
  DrawerContent,
  // DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "@/components/ui/drawer";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Link, useNavigate, useLocation } from "react-router";
import {
  LogOut,
  FileTextIcon,
  UserIcon,
  LucideIcon,
  Menu,
  Globe,
  ChevronDown,
  Upload,
  Plus,
  BarChart3,
  Database
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useAuthenticator } from "@aws-amplify/ui-react";
import { useTranslation } from "react-i18next";
import { languages } from "@/lib/i18n";
import { useMediaQuery } from "@/hooks/use-media-query";
import Logo from "@/assets/aws.svg";

interface NavBarProps extends React.HTMLAttributes<HTMLDivElement> {
  icon?: LucideIcon;
  onNewAnalysis?: () => void
  onKnowledgeBase?: () => void
}


export default function Navbar({
  className,
  icon: Icon = FileTextIcon,
  onNewAnalysis,
  onKnowledgeBase,
  ...props
}: NavBarProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const { t, i18n } = useTranslation();
  const location = useLocation();

  const isDesktop = useMediaQuery("(min-width: 768px)");

  const {
    user: { username },
    signOut,
  } = useAuthenticator((context) => [context.user]);

  const navigate = useNavigate();

  const handleSignOut = async () => {
    try {
      // If you need to clear anything in the user's session, do it here

      await signOut();
      navigate("/");
      setMenuOpen(false);
    } catch (error) {
      console.error(error);
    }
  };

  const handleLanguageChange = (langCode: string) => {
    i18n.changeLanguage(langCode);
    setMenuOpen(false);
  };

  
  const AppLogo = (
    <div className="flex items-center space-x-4">
      <Link
        to="/"
        className="flex w-8 justify-center sm:w-10 md:block"
      >
        <img src={Logo} alt="AWS" />
      </Link>
      <Link
        to="/"
        className="flex items-center gap-1 text-lg font-bold md:gap-2"

      >
        <Icon className="h-5 w-5 sm:h-6 sm:w-6" />
        <span className="text-xs sm:text-sm md:text-base">
          {t("app.title")}
        </span>
      </Link>
      
      {/* Navigation Items - Desktop Only */}
      {isDesktop && (
        <nav className="flex items-center space-x-1 ml-6">
          <Link
            to="/analysis"
            className={cn(
              "px-4 py-2 text-sm font-medium rounded-md transition-colors",
              location.pathname === "/" || location.pathname === "/analysis"
                ? "bg-violet-100 text-violet-700 hover:bg-violet-200"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            )}
          >
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              {t('navbar.analysis')}
            </div>
          </Link>
          <Link
            to="/knowledge-base"
            className={cn(
              "px-4 py-2 text-sm font-medium rounded-md transition-colors",
              location.pathname === "/knowledge-base"
                ? "bg-violet-100 text-violet-700 hover:bg-violet-200"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            )}
          >
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4" />
              {t('navbar.knowledgeBase')}
            </div>
          </Link>
        </nav>
      )}
    </div>
  );

  const LanguageOptions = ({ mobile = false }: { mobile?: boolean }) => (
    <>
      {mobile ? (
        <div className="flex w-full flex-col">
          <Button
            variant="outline"
            className="w-full justify-start"
            onClick={() =>
              document.getElementById("languageAccordion")?.click()
            }
          >
            <Globe className="mr-2 h-4 w-4" />
            <span>{t("language.changeLanguage")}</span>
          </Button>
          <Accordion type="single" collapsible className="w-full border-none">
            <AccordionItem value="languages" className="border-none">
              <AccordionTrigger
                className="sr-only p-0 hover:no-underline"
                id="languageAccordion"
              >
                <span className="sr-only">{t("language.changeLanguage")}</span>
              </AccordionTrigger>
              <AccordionContent className="pb-0 pt-2">
                <div className="grid grid-cols-2 gap-2">
                  {languages.map((lang) => (
                    <Button
                      key={lang.code}
                      variant={
                        lang.code === i18n.language ? "default" : "outline"
                      }
                      size="sm"
                      className="justify-start"
                      onClick={() => handleLanguageChange(lang.code)}
                    >
                      <span className="mr-2">{lang.flag}</span>
                      <span>{lang.nativeName}</span>
                    </Button>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      ) : (
        <DropdownMenuSub>
          <DropdownMenuSubTrigger className="cursor-pointer">
            <Globe className="mr-2 h-4 w-4" />
            <span>{t("language.changeLanguage")}</span>
          </DropdownMenuSubTrigger>
          <DropdownMenuPortal>
            <DropdownMenuSubContent className="w-48">
              {languages.map((lang) => (
                <DropdownMenuItem
                  key={lang.code}
                  className={cn(
                    "flex cursor-pointer items-center",
                    lang.code === i18n.language && "bg-muted",
                  )}
                  onClick={() => handleLanguageChange(lang.code)}
                >
                  <span className="mr-2">{lang.flag}</span>
                  <span className="text-sm">{lang.nativeName}</span>
                </DropdownMenuItem>
              ))}
            </DropdownMenuSubContent>
          </DropdownMenuPortal>
        </DropdownMenuSub>
      )}
    </>
  );

  return (
    <>
      <header
        className={cn(
          "sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-background px-4 shadow-sm md:px-6",
          className,
        )}
        {...props}
      >
        {AppLogo}

        <div className="flex items-center gap-2 md:gap-4">
          {isDesktop ? (
            <>
              <div className="mr-4 flex items-center space-x-4">
                {/* Show Knowledge Base button only when on knowledge-base route */}
                {location.pathname === "/knowledge-base" && (
                  <Button
                    onClick={onKnowledgeBase}
                    className="flex items-center gap-2 text-sm font-semibold bg-gradient-to-r from-[#742ed1] via-[#6f37d4] to-[#4d7ceb] hover:from-[#6a29c4] hover:via-[#6530c7] hover:to-[#4570de] active:from-[#5f24b7] active:via-[#5b29ba] active:to-[#3d63d1] transition-all duration-200 shadow-lg hover:shadow-xl active:scale-95"
                  >
                    <Upload className="w-4 h-4" />
                    {t('knowledgeBase.addDocument')}
                  </Button>
                )}
                
                {/* Show New Analysis button only when on analysis route */}
                {(location.pathname === "/" || location.pathname === "/analysis") && (
                  <Button
                    onClick={onNewAnalysis}
                    className="flex items-center gap-2 text-sm font-semibold bg-gradient-to-r from-[#742ed1] via-[#6f37d4] to-[#4d7ceb] hover:from-[#6a29c4] hover:via-[#6530c7] hover:to-[#4570de] active:from-[#5f24b7] active:via-[#5b29ba] active:to-[#3d63d1] transition-all duration-200 shadow-lg hover:shadow-xl active:scale-95"
                  >
                    <Plus className="w-4 h-4" />
                    {t('navbar.newAnalysis')}
                  </Button>
                )}
              </div>
              <DropdownMenu open={menuOpen} onOpenChange={setMenuOpen}>
                <DropdownMenuTrigger asChild>
                  <div className="flex items-center">
                    <Avatar className="h-10 w-10 cursor-pointer">
                      <AvatarImage src={`https://github.com/${username}.png`} />
                      <AvatarFallback>
                        {username ? (
                          username.substring(0, 2).toUpperCase()
                        ) : (
                          <UserIcon className="h-4 w-4" />
                        )}
                      </AvatarFallback>
                    </Avatar>
                    <ChevronDown className="ml-1 h-4 w-4 text-muted-foreground" />
                  </div>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end">
                  <DropdownMenuLabel>
                    {username
                      ? t("user.loggedInAs", { username })
                      : t("user.menu")}
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <LanguageOptions />
                  <DropdownMenuItem
                    className="cursor-pointer"
                    onClick={handleSignOut}
                  >
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>{t("user.logout")}</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          ) : (
            <Drawer open={menuOpen} onOpenChange={setMenuOpen}>
              <DrawerTrigger asChild>
                <Button variant="ghost" size="icon" aria-label={t('navbar.toggleMenu')}>
                  <Menu className="h-5 w-5" />
                </Button>
              </DrawerTrigger>
              <DrawerContent className="h-[85vh]">
                <DrawerHeader>
                  <DrawerTitle>{t("app.title")}</DrawerTitle>
                  {/* <DrawerDescription>{t("app.description")}</DrawerDescription> */}
                </DrawerHeader>
                <div className="flex-1 overflow-y-auto px-4 py-2">
                  <nav className="flex flex-col space-y-2">
                    <Link
                      to="/analysis"
                      className={cn(
                        "flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors",
                        location.pathname === "/" || location.pathname === "/analysis"
                          ? "bg-violet-100 text-violet-700"
                          : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                      )}
                      onClick={() => setMenuOpen(false)}
                    >
                      <BarChart3 className="w-5 h-5" />
                      {t('navbar.analysis')}
                    </Link>
                    <Link
                      to="/knowledge-base"
                      className={cn(
                        "flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors",
                        location.pathname === "/knowledge-base"
                          ? "bg-violet-100 text-violet-700"
                          : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                      )}
                      onClick={() => setMenuOpen(false)}
                    >
                      <Database className="w-5 h-5" />
                      {t('navbar.knowledgeBase')}
                    </Link>
                  </nav>
                </div>
                <DrawerFooter className="flex flex-col gap-2 space-y-0">
                  <LanguageOptions mobile />
                  <Button
                    variant="outline"
                    className="w-full justify-start"
                    onClick={handleSignOut}
                  >
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>{t("user.logout")}</span>
                  </Button>
                </DrawerFooter>
              </DrawerContent>
            </Drawer>
          )}
        </div>
      </header>

    </>
  );
}

export { Navbar };
