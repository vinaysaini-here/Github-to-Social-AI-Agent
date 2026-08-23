import { DraftList } from "./components/DraftList";

function App() {
  return (
    <div className="min-h-screen bg-paper">
      <header className="border-b border-line px-4 py-4">
        <h1 className="max-w-2xl mx-auto text-lg font-semibold text-ink">Approval Inbox</h1>
      </header>
      <DraftList />
    </div>
  );
}

export default App;