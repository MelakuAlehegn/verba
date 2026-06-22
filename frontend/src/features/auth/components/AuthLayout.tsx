import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { AuthBrandingPanel } from "@/features/auth/components/AuthBrandingPanel";

interface AuthLayoutProps {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer?: ReactNode;
}

export function AuthLayout({ title, subtitle, children, footer }: AuthLayoutProps) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <AuthBrandingPanel className="hidden lg:flex" />

      <div className="relative flex min-h-screen flex-col bg-background">
        <div className="absolute right-4 top-4 z-10 sm:right-6 sm:top-6">
          <ThemeToggle />
        </div>

        <div className="flex flex-1 flex-col justify-center px-6 py-16 sm:px-10 lg:px-16">
          <div className="mx-auto w-full max-w-sm animate-fade-in">
            <div className="mb-8 lg:hidden">
              <Link to="/" className="text-lg font-semibold tracking-tight text-foreground">
                Verba
              </Link>
            </div>

            <div className="mb-8">
              <h1 className="text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{subtitle}</p>
            </div>

            {children}

            {footer ? <div className="mt-8 text-center text-sm text-muted-foreground">{footer}</div> : null}
          </div>
        </div>
      </div>
    </div>
  );
}
