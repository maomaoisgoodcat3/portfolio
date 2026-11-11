import type { Block } from "@/lib/api";
import { str, strList } from "@/lib/fields";
import { safeHref } from "@/lib/safe-url";

type Props = { block: Block };

export function StatsBlock({ block }: Props) {
  const provider = str(block.props, "provider");
  const account = str(block.props, "account");
  const show = strList(block.props, "show");
  const visibleMetrics = show.length > 0 ? show : ["repos", "stars", "contributions", "languages"];
  const stats = block.stats;
  const githubHref = safeHref(
    account ? `https://github.com/${encodeURIComponent(account)}` : "",
  );
  const activeParts = stats?.data.active_parts;
  const mostActive = activeParts
    ? (Object.entries(activeParts).sort(([, first], [, second]) => second - first)[0]?.[0] ?? null)
    : null;
  const activeLabels: Record<string, string> = {
    night: "night (0-6, UTC+7)",
    morning: "morning (6-12, UTC+7)",
    afternoon: "afternoon (12-18, UTC+7)",
    evening: "evening (18-24, UTC+7)",
  };
  const dateFormatter = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Ho_Chi_Minh",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
  const formattedDate = stats
    ? dateFormatter
        .formatToParts(new Date(stats.fetched_at))
        .filter(({ type }) => type !== "literal")
        .map(({ value }) => value)
        .join("/")
        .replace(/(\d{2})\/(\d{2})\/(\d{4})\/(\d{2})\/(\d{2})/, "$1/$2/$3 $4:$5")
    : null;

  return (
    <article className="pixel-box w-full bg-surface p-4 text-text">
      <h3 className="font-pixel text-xl text-accent">{block.title}</h3>
      {(provider || account) && <p className="mt-1 text-sm text-muted">{[provider, account].filter(Boolean).join(" · ")}</p>}
      {stats === null || stats === undefined ? (
        <p className="mt-2 text-muted">Stats coming soon</p>
      ) : (
        <>
          <div className="mt-3 grid min-w-0 grid-cols-2 gap-2 sm:grid-cols-4">
            {visibleMetrics.includes("repos") && (
              <div className="pixel-box min-w-0 p-2 text-center">
                <div className="font-pixel text-2xl text-accent">{stats.data.public_repos}</div>
                <div className="text-xs text-muted">Repos</div>
              </div>
            )}
            {visibleMetrics.includes("stars") && (
              <div className="pixel-box min-w-0 p-2 text-center">
                <div className="font-pixel text-2xl text-accent">{stats.data.stars}</div>
                <div className="text-xs text-muted">Stars</div>
              </div>
            )}
            {visibleMetrics.includes("contributions") && stats.data.contributions_last_year !== null && (
              <div className="pixel-box min-w-0 p-2 text-center">
                <div className="font-pixel text-2xl text-accent">{stats.data.contributions_last_year}</div>
                <div className="text-xs text-muted">Contributions</div>
              </div>
            )}
            {visibleMetrics.includes("languages") && (
              <div className="pixel-box min-w-0 p-2 text-center">
                <div className="font-pixel text-2xl text-accent">{stats.data.top_languages.length}</div>
                <div className="text-xs text-muted">Languages</div>
                <div className="mt-1 flex flex-wrap justify-center gap-1">
                  {stats.data.top_languages.map((language) => (
                    <span key={language} className="rounded border border-current px-1 text-xs text-muted">
                      {language}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
          {visibleMetrics.includes("active_hours") && mostActive && (
            <p className="mt-3 text-sm text-muted">Most active: {activeLabels[mostActive]}</p>
          )}
          <p className="mt-3 text-sm text-muted">
            Updated {formattedDate}
          </p>
          {githubHref && (
            <a className="mt-2 inline-block text-accent underline" href={githubHref} target="_blank" rel="noreferrer">
              View on GitHub
            </a>
          )}
        </>
      )}
    </article>
  );
}
