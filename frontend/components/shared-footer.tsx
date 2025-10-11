"use client"

import Link from 'next/link'
import { Scale } from 'lucide-react'
import { useLanguage } from '@/contexts/language-context'

export function SharedFooter() {
  const { t } = useLanguage()

  return (
    <footer className="bg-background border-t border-border py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Scale className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold text-foreground">ARTISTING</span>
            </div>
            <p className="text-muted-foreground">{t("footer.description")}</p>
          </div>
          <div>
            <h3 className="font-semibold mb-4 text-foreground">{t("footer.product")}</h3>
            <ul className="space-y-2 text-muted-foreground">
              <li>
                <Link href="/features" className="hover:text-foreground transition-colors">
                  {t("footer.features")}
                </Link>
              </li>
              <li>
                <Link href="/pricing" className="hover:text-foreground transition-colors">
                  {t("footer.pricing")}
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold mb-4 text-foreground">{t("footer.legal")}</h3>
            <ul className="space-y-2 text-muted-foreground">
              <li>
                <Link href="/terms" className="hover:text-foreground transition-colors">
                  {t("footer.terms")}
                </Link>
              </li>
              <li>
                <Link href="/privacy" className="hover:text-foreground transition-colors">
                  {t("footer.privacy")}
                </Link>
              </li>
              <li>
                <Link href="/cookies" className="hover:text-foreground transition-colors">
                  {t("footer.cookies")}
                </Link>
              </li>
              <li>
                <Link href="/gdpr" className="hover:text-foreground transition-colors">
                  {t("footer.gdpr")}
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold mb-4 text-foreground">{t("footer.support")}</h3>
            <ul className="space-y-2 text-muted-foreground">
              <li>
                <Link href="/help" className="hover:text-foreground transition-colors">
                  {t("footer.help")}
                </Link>
              </li>
              <li>
                <Link href="/contact" className="hover:text-foreground transition-colors">
                  {t("footer.contact")}
                </Link>
              </li>
              <li>
                <Link href="/status" className="hover:text-foreground transition-colors">
                  {t("footer.status")}
                </Link>
              </li>
              <li>
                <Link href="/community" className="hover:text-foreground transition-colors">
                  {t("footer.community")}
                </Link>
              </li>
            </ul>
          </div>
        </div>
        <div className="border-t border-border mt-8 pt-8 text-center text-muted-foreground">
          <p>&copy; 2024 ARTISTING. {t("footer.rights")}</p>
        </div>
      </div>
    </footer>
  )
}
