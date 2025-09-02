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

import React from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";

export function HelloWorld(): React.ReactElement {
  const { t, i18n } = useTranslation();

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-8">
        <div className="w-full max-w-2xl bg-card border border-border rounded-lg shadow-sm">
          <div className="p-6 text-center">
            <h1 className="text-4xl font-bold text-primary mb-2">
              {t("helloWorld.title", "Hello World")}
            </h1>
            <p className="text-lg text-muted-foreground">
              {t("helloWorld.subtitle", "Bem-vindo ao seu novo projeto!")}
            </p>
          </div>
          <div className="p-6 pt-0 space-y-6">
            <div className="text-center">
              <p className="text-muted-foreground">
                {t("helloWorld.description", "Este é um projeto base limpo com autenticação AWS Amplify e internacionalização configurada.")}
              </p>
            </div>
            
            <div className="flex flex-col items-center space-y-4">
              <p className="text-sm font-medium">
                {t("helloWorld.languageSelect", "Escolha o idioma:")}
              </p>
              <div className="flex space-x-2">
                <Button
                  variant={i18n.language === "pt_BR" ? "default" : "outline"}
                  size="sm"
                  onClick={() => changeLanguage("pt_BR")}
                >
                  🇧🇷 Português
                </Button>
                <Button
                  variant={i18n.language === "en" ? "default" : "outline"}
                  size="sm"
                  onClick={() => changeLanguage("en")}
                >
                  🇺🇸 English
                </Button>
                <Button
                  variant={i18n.language === "es" ? "default" : "outline"}
                  size="sm"
                  onClick={() => changeLanguage("es")}
                >
                  🇪🇸 Español
                </Button>
              </div>
            </div>

            <div className="pt-4 border-t">
              <h3 className="text-lg font-semibold mb-2">
                {t("helloWorld.features.title", "Recursos incluídos:")}
              </h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>✅ {t("helloWorld.features.auth", "Autenticação AWS Amplify/Cognito")}</li>
                <li>✅ {t("helloWorld.features.i18n", "Internacionalização (PT, EN, ES)")}</li>
                <li>✅ {t("helloWorld.features.ui", "Componentes UI (shadcn/ui)")}</li>
                <li>✅ {t("helloWorld.features.routing", "Roteamento React Router")}</li>
                <li>✅ {t("helloWorld.features.styling", "Styling com Tailwind CSS")}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
