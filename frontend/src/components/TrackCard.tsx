import type { EmotionName, Track } from "../types";

const emotionNames: Record<EmotionName, string> = {
  joy: "радость",
  sadness: "грусть",
  calm: "спокойствие",
  energy: "энергия",
  romance: "романтика",
  anxiety: "напряжение",
};

type TrackCardProps = {
  track: Track;
  index: number;
  favorite: boolean;
  onToggleFavorite: (track: Track) => void;
  authenticated: boolean;
};

export function TrackCard({ track, index, favorite, onToggleFavorite, authenticated }: TrackCardProps) {
  const scoreParts = track.score_breakdown;
  const scoreDetails = scoreParts
    ? [
        scoreParts.semantic !== null && scoreParts.semantic !== undefined ? ["смысл", scoreParts.semantic] as const : null,
        scoreParts.lexical !== null && scoreParts.lexical !== undefined ? ["слова", scoreParts.lexical] as const : null,
        scoreParts.emotion !== null && scoreParts.emotion !== undefined ? ["эмоции", scoreParts.emotion] as const : null,
      ].filter((part): part is readonly [string, number] => part !== null)
    : [];
  const emotions = (Object.entries(track.emotion_scores ?? {}) as [EmotionName, number][])
    .filter(([, value]) => value >= 0.35)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 2);

  return (
    <article className="track-card">
      <div className={`cover cover-${(index % 6) + 1}`} aria-hidden="true">
        <span className="cover-note">♫</span>
        <span className="cover-index">{String(index + 1).padStart(2, "0")}</span>
        <span className="cover-orbit" />
      </div>
      <div className="track-info">
        <div className="track-title-row">
          <div className="track-title-block">
            <h3>{track.title}</h3>
            <p className="artist">{track.artist}</p>
          </div>
          {track.score > 0 && <span className="match-score" title="Итоговая оценка ранжирования">{Math.round(track.score * 100)}%</span>}
        </div>
        <p className="track-description">{track.description}</p>
        {scoreDetails.length > 0 && (
          <div className="score-details" aria-label="Составляющие оценки соответствия">
            {scoreDetails.map(([label, value]) => <span key={label}>{label} <b>{Math.round(value * 100)}%</b></span>)}
          </div>
        )}
        <div className="track-bottom">
          <div className="tags">
            <span className="tag genre-tag">{track.genre}</span>
            {emotions.map(([name]) => <span className="tag" key={name}>{emotionNames[name]}</span>)}
          </div>
          <button
            className={`favorite-button ${favorite ? "is-favorite" : ""}`}
            type="button"
            aria-label={favorite ? `Убрать ${track.title} из избранного` : `Добавить ${track.title} в избранное`}
            title={authenticated ? (favorite ? "Убрать из избранного" : "В избранное") : "Войдите, чтобы сохранить"}
            onClick={() => onToggleFavorite(track)}
          >
            {favorite ? "♥" : "♡"}
          </button>
        </div>
        {track.listening_url && (
          <a className="listen-link" href={track.listening_url} target="_blank" rel="noreferrer">Открыть источник ↗</a>
        )}
      </div>
    </article>
  );
}
