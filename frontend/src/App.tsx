import { useEffect, useMemo, useState } from "react";
import { AuthDialog } from "./components/AuthDialog";
import { TrackCard } from "./components/TrackCard";
import { api, getToken, saveToken } from "./services/api";
import type { SearchHistoryEntry, SearchResponse, Track, User } from "./types";

type View = "search" | "catalog" | "favorites" | "history";

const suggestions = [
  "меланхоличная музыка для дождливого вечера",
  "спокойный звук для чтения и отдыха",
  "энергичная музыка для тренировки",
  "романтичный вечер в городе",
];

const viewTitles: Record<Exclude<View, "search">, { eyebrow: string; title: string; copy: string }> = {
  catalog: { eyebrow: "ОТКРЫВАЙ НОВОЕ", title: "Каталог композиций", copy: "Исследуй подборку и добавляй понравившееся в избранное." },
  favorites: { eyebrow: "ТВОЯ КОЛЛЕКЦИЯ", title: "Избранное", copy: "Композиции, которые хочется сохранить рядом." },
  history: { eyebrow: "ТВОИ МУЗЫКАЛЬНЫЕ МОМЕНТЫ", title: "История поиска", copy: "Возвращайся к прошлым настроениям и запросам." },
};

export default function App() {
  const [view, setView] = useState<View>("search");
  const [query, setQuery] = useState("");
  const [genre, setGenre] = useState("");
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);
  const [catalog, setCatalog] = useState<Track[]>([]);
  const [favorites, setFavorites] = useState<Track[]>([]);
  const [history, setHistory] = useState<SearchHistoryEntry[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [authOpen, setAuthOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(false);
  const [catalogLoaded, setCatalogLoaded] = useState(false);
  const [error, setError] = useState("");

  const favoriteIds = useMemo(() => new Set(favorites.map((track) => track.id)), [favorites]);
  const catalogGenres = useMemo(() => [...new Set(catalog.map((track) => track.genre))].sort(), [catalog]);

  useEffect(() => {
    api.tracks().then(setCatalog).catch(() => undefined).finally(() => setCatalogLoaded(true));
    if (!getToken()) return;
    api.me().then(setUser).catch(() => saveToken(null));
    api.favorites().then(setFavorites).catch(() => undefined);
  }, []);

  async function search(nextQuery = query) {
    if (nextQuery.trim().length < 2) return;
    setView("search");
    setQuery(nextQuery);
    setLoading(true);
    setError("");
    try {
      setSearchResult(await api.search(nextQuery.trim(), genre || null));
      if (user) api.history().then(setHistory).catch(() => undefined);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Поиск завершился с ошибкой.");
      setSearchResult(null);
    } finally {
      setLoading(false);
    }
  }

  async function openView(nextView: View) {
    setView(nextView);
    setError("");
    if ((nextView === "favorites" || nextView === "history") && !user) {
      setAuthOpen(true);
      return;
    }
    if (nextView === "search") return;
    setPageLoading(true);
    try {
      if (nextView === "catalog") setCatalog(await api.tracks());
      if (nextView === "favorites") setFavorites(await api.favorites());
      if (nextView === "history") setHistory(await api.history());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Не удалось загрузить раздел.");
    } finally {
      setPageLoading(false);
    }
  }

  async function toggleFavorite(track: Track) {
    if (!user) {
      setAuthOpen(true);
      return;
    }
    const wasFavorite = favoriteIds.has(track.id);
    try {
      if (wasFavorite) {
        await api.removeFavorite(track.id);
        setFavorites((current) => current.filter((item) => item.id !== track.id));
      } else {
        await api.addFavorite(track.id);
        setFavorites((current) => [...current, { ...track, is_favorite: true }]);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Не удалось обновить избранное.");
    }
  }

  function onAuthenticated(authUser: User) {
    setUser(authUser);
    setAuthOpen(false);
    api.favorites().then(setFavorites).catch(() => setFavorites([]));
    if (view === "history") api.history().then(setHistory).catch(() => undefined);
  }

  function logout() {
    saveToken(null);
    setUser(null);
    setFavorites([]);
    if (view === "favorites" || view === "history") setView("search");
  }

  function renderTracks(tracks: Track[]) {
    return (
      <div className="track-grid">
        {tracks.map((track, index) => (
          <TrackCard
            key={track.id}
            track={track}
            index={index}
            favorite={favoriteIds.has(track.id)}
            authenticated={Boolean(user)}
            onToggleFavorite={toggleFavorite}
          />
        ))}
      </div>
    );
  }

  return (
    <main className="app-shell" id="top">
      <header className="topbar">
        <a className="brand" href="#top" onClick={() => openView("search")} aria-label="Melodia — главная">
          <span className="brand-mark">♫</span><span>melodia</span>
        </a>
        <nav className="main-nav" aria-label="Основная навигация">
          {(["search", "catalog", "favorites", "history"] as View[]).map((item) => (
            <button className={`nav-link ${view === item ? "active" : ""}`} key={item} onClick={() => openView(item)}>
              {{ search: "Поиск", catalog: "Каталог", favorites: "Избранное", history: "История" }[item]}
              {item === "favorites" && favorites.length > 0 && <span className="nav-count">{favorites.length}</span>}
            </button>
          ))}
        </nav>
        <div className="account-area">
          <span className="prototype-label">MVP</span>
          {user ? (
            <button className="account-button" type="button" onClick={logout} title="Выйти из аккаунта" aria-label={`Выйти из аккаунта ${user.display_name}`}>
              <span className="avatar">{user.display_name.trim().slice(0, 1).toUpperCase()}</span>
              <span className="account-name">{user.display_name}</span>
              <span className="logout-mark" aria-hidden="true">↪</span>
            </button>
          ) : (
            <button className="login-button" type="button" onClick={() => setAuthOpen(true)}>Войти</button>
          )}
        </div>
      </header>

      {view === "search" ? (
        <>
          <section className="hero">
            <div className="hero-glow" aria-hidden="true" />
            <p className="eyebrow">МУЗЫКА, КОТОРАЯ ПОНИМАЕТ НАСТРОЕНИЕ</p>
            <h1>Опиши момент.<br /><span>Найди свой звук.</span></h1>
            <p className="intro">Расскажи, какую музыку хочется услышать. Melodia сопоставит смысл запроса, эмоции и жанр.</p>
            <form className="search-form" onSubmit={(event) => { event.preventDefault(); void search(); }}>
              <span className="search-icon" aria-hidden="true">⌕</span>
              <label className="sr-only" htmlFor="music-query">Опиши желаемую музыку</label>
              <input
                id="music-query"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Например: спокойная музыка для прогулки под дождём"
                minLength={2}
                maxLength={500}
              />
              <select aria-label="Фильтр по жанру" value={genre} onChange={(event) => setGenre(event.target.value)}>
                <option value="">Все жанры</option>
                {catalogGenres.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
              <button className="primary-button" type="submit" disabled={loading || query.trim().length < 2}>
                {loading ? <><span className="spinner" /> Ищем</> : <>Найти музыку <span aria-hidden="true">↗</span></>}
              </button>
            </form>
            <div className="suggestions">
              <span>ПОПРОБУЙ:</span>
              {suggestions.map((item) => <button key={item} type="button" onClick={() => { setQuery(item); void search(item); }}>{item}</button>)}
            </div>
          </section>

          <section className="content-section search-results" aria-live="polite">
            <div className="section-heading">
              <div>
                <p className="eyebrow">{searchResult ? "ПОДБОРКА ДЛЯ ТЕБЯ" : "ТВОЯ МУЗЫКАЛЬНАЯ ИДЕЯ"}</p>
                <h2>{searchResult ? "Результаты поиска" : "Найди музыку под своё состояние"}</h2>
              </div>
              {searchResult && <span className="result-count">{searchResult.results.length} композиций</span>}
            </div>
            {searchResult?.mode === "lexical_fallback" && (
              <div className="notice warning"><span>i</span><p>Модель семантического поиска не загрузилась — использован резервный поиск по словам. {searchResult.notice}</p></div>
            )}
            {searchResult?.mode === "hybrid" && searchResult.emotion_mode === "lexicon" && (
              <div className="notice info"><span>i</span><p>Семантический поиск работает; эмоциональные оценки сейчас определяются лексическим классификатором.</p></div>
            )}
            {error && <div className="notice error"><span>!</span><p>{error}</p></div>}
            {loading && <div className="loading-panel"><span className="spinner large" /> Сопоставляем смысл и эмоциональные характеристики…</div>}
            {!loading && searchResult?.results.length === 0 && <EmptyState title="Пока нет совпадений" copy="Попробуй переформулировать запрос или снять жанровый фильтр." />}
            {!loading && searchResult && searchResult.results.length > 0 && renderTracks(searchResult.results)}
            {!loading && !searchResult && <div className="empty-state welcome-state"><div className="sound-orbit">♫</div><div><h3>Расскажи, что хочется услышать</h3><p>{catalogLoaded && catalog.length === 0 ? "Каталог пока пуст. Импортируй свои композиции из CSV, чтобы Melodia могла искать по ним." : "Подборка будет учитывать смысл описания и эмоциональный профиль композиции."}</p></div></div>}
          </section>
        </>
      ) : (
        <section className="content-section page-content">
          <div className="page-heading">
            <div>
              <p className="eyebrow">{viewTitles[view].eyebrow}</p>
              <h1>{viewTitles[view].title}</h1>
              <p className="intro">{viewTitles[view].copy}</p>
            </div>
            {view === "catalog" && <span className="result-count">{catalog.length} композиций</span>}
          </div>
          {error && <div className="notice error"><span>!</span><p>{error}</p></div>}
          {pageLoading && <div className="loading-panel"><span className="spinner large" /> Загружаем…</div>}
          {!pageLoading && view === "catalog" && (catalog.length ? renderTracks(catalog) : <EmptyState title="Каталог пока пуст" copy="Импортируй свои композиции из CSV, чтобы они появились здесь." />)}
          {!pageLoading && view === "favorites" && (favorites.length ? renderTracks(favorites) : <EmptyState title="Избранное пока пусто" copy="Нажми на сердечко у понравившейся композиции, чтобы сохранить её." />)}
          {!pageLoading && view === "history" && (
            history.length ? <div className="history-list">{history.map((item) => (
              <button className="history-item" key={item.id} onClick={() => { setQuery(item.query); void search(item.query); }}>
                <span className="history-icon">⌕</span>
                <span className="history-query">{item.query}</span>
                <time>{new Date(item.created_at).toLocaleDateString("ru-RU", { day: "numeric", month: "short" })}</time>
                <span className="history-arrow">↗</span>
              </button>
            ))}</div> : <EmptyState title="История появится после поиска" copy="Выполненные запросы будут сохраняться в этом разделе." />
          )}
        </section>
      )}

      <footer className="footer">
        <a className="footer-brand" href="#top"><span className="brand-mark">♫</span> melodia</a>
        <span>Интеллектуальный поиск музыки · Курсовой проект</span>
        <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">API документация ↗</a>
      </footer>

      {authOpen && <AuthDialog onClose={() => setAuthOpen(false)} onAuthenticated={onAuthenticated} />}
    </main>
  );
}

function EmptyState({ title, copy }: { title: string; copy: string }) {
  return <div className="empty-state"><div className="sound-orbit">♫</div><div><h3>{title}</h3><p>{copy}</p></div></div>;
}
