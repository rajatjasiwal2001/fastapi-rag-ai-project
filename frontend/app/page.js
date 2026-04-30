import ChatBox from "../components/ChatBox";
import FileUpload from "../components/FileUpload";

export default function HomePage() {
  return (
    <main className="min-h-screen px-4 py-8 md:px-8">
      <div className="mx-auto grid w-full max-w-6xl grid-cols-1 gap-6 lg:grid-cols-3">
        <section className="lg:col-span-1">
          <FileUpload />
        </section>

        <section className="lg:col-span-2">
          <ChatBox />
        </section>
      </div>
    </main>
  );
}
