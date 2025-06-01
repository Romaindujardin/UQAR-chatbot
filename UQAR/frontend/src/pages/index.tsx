import { useEffect } from "react";
import { useRouter } from "next/router";
import Head from "next/head";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Rediriger vers la page de connexion
    router.push("/login");
  }, [router]);

  return (
    <>
      <Head>
        <title>Assistant Éducatif UQAR</title>
        <meta
          name="description"
          content="Assistant éducatif local avec RAG pour l'UQAR"
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="spinner w-8 h-8 mx-auto mb-4"></div>
          <p className="text-gray-600">Redirection en cours...</p>
        </div>
      </div>
    </>
  );
}
