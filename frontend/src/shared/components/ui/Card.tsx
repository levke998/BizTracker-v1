import type { HTMLAttributes, ReactNode } from "react";

type CardTone = "default" | "primary" | "secondary" | "highlight" | "rainbow";
type CardElement = "article" | "section" | "div";

type CardProps = Omit<HTMLAttributes<HTMLElement>, "title"> & {
  as?: CardElement;
  title?: ReactNode;
  subtitle?: ReactNode;
  eyebrow?: ReactNode;
  actions?: ReactNode;
  count?: ReactNode;
  tone?: CardTone;
  hoverable?: boolean;
};

function joinClassNames(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function Card({
  as = "section",
  title,
  subtitle,
  eyebrow,
  actions,
  count,
  tone = "default",
  hoverable = false,
  className,
  children,
  ...props
}: CardProps) {
  const Component = as;

  return (
    <Component
      className={joinClassNames(
        "card",
        tone !== "default" && `card-${tone}`,
        hoverable && "card-hover",
        className,
      )}
      {...props}
    >
      {title || subtitle || eyebrow || actions || count ? (
        <div className="card-header">
          <div className="card-heading">
            {eyebrow ? <span className="card-eyebrow">{eyebrow}</span> : null}
            {title ? <h2 className="card-title">{title}</h2> : null}
            {subtitle ? <p className="card-subtitle">{subtitle}</p> : null}
          </div>
          {actions ?? (count ? <span className="card-count">{count}</span> : null)}
        </div>
      ) : null}
      {children}
    </Component>
  );
}
