import { Link } from "react-router";
import Layout from "../components/Layout";

export default function NotFoundPage({ message = "Page not found" }: { message?: string }) {
  return (
    <Layout>
      <h1>{message}</h1>
      <p>
        <Link to="/">Back to start</Link>
      </p>
    </Layout>
  );
}
