import { Link } from 'react-router-dom';

export function NotFoundRoute() {
  return (
    <section className="rat-page">
      <h1>404</h1>
      <p>That route doesn't exist yet.</p>
      <Link to="/">Back to home</Link>
    </section>
  );
}
