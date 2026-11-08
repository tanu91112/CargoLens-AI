import { useEffect, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [user, setUser] = useState(null);
  const [shipments, setShipments] = useState([]);
  const [activePage, setActivePage] = useState("Dashboard");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [shipmentNumber, setShipmentNumber] = useState("");
  const [supplier, setSupplier] = useState("");
  const [origin, setOrigin] = useState("");

  const [exportShipmentId, setExportShipmentId] = useState("");
  const [exporting, setExporting] = useState(false);

  async function apiRequest(path, options = {}) {
    const currentToken = localStorage.getItem("token") || token;

    const headers = {
      ...(options.body && !(options.body instanceof FormData)
        ? { "Content-Type": "application/json" }
        : {}),
      ...(currentToken ? { Authorization: `Bearer ${currentToken}` } : {}),
      ...options.headers,
    };

    const response = await fetch(`${API}${path}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || "Something went wrong");
    }

    return response.json();
  }

  async function loadShipments() {
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest("/shipments");
      setShipments(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadUser() {
    try {
      const data = await apiRequest("/auth/me");
      setUser(data);
      await loadShipments();
    } catch {
      localStorage.removeItem("token");
      setToken("");
      setUser(null);
    }
  }

  useEffect(() => {
    if (token) loadUser();
  }, []);

  async function handleLogin(event) {
    event.preventDefault();
    setError("");

    try {
      const response = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Login failed");
      }

      localStorage.setItem("token", data.access_token);
      setToken(data.access_token);

      const profile = await fetch(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });

      if (!profile.ok) throw new Error("Could not load user profile");

      setUser(await profile.json());
      await loadShipments();
    } catch (err) {
      setError(err.message);
    }
  }

  function handleLogout() {
    localStorage.removeItem("token");
    setToken("");
    setUser(null);
    setShipments([]);
  }

  async function createShipment(event) {
    event.preventDefault();
    setError("");

    try {
      await apiRequest("/shipments", {
        method: "POST",
        body: JSON.stringify({
          shipment_number: shipmentNumber,
          supplier_name: supplier,
          origin_country: origin,
        }),
      });

      setShipmentNumber("");
      setSupplier("");
      setOrigin("");
      await loadShipments();
      setActivePage("Shipments");
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleExportCsv() {
    if (!exportShipmentId) {
      setError("Please select a shipment to export.");
      return;
    }

    setError("");
    setExporting(true);

    try {
      const currentToken = localStorage.getItem("token") || token;

      const response = await fetch(
        `${API}/shipments/${exportShipmentId}/export`,
        {
          headers: { Authorization: `Bearer ${currentToken}` },
        }
      );

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || "CSV export failed.");
      }

      const selected = shipments.find(
        (s) => String(s.id) === String(exportShipmentId)
      );
      const fileLabel = selected
        ? selected.shipment_number
        : `shipment-${exportShipmentId}`;

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = url;
      link.download = `${fileLabel}_export.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    } finally {
      setExporting(false);
    }
  }

  const filteredShipments = shipments.filter((shipment) =>
    `${shipment.shipment_number} ${shipment.supplier_name}`
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  if (!token || !user) {
    return (
      <div className="login-page">
        <form className="login-card" onSubmit={handleLogin}>
          <div className="brand-icon">C</div>
          <h1>CargoLens AI</h1>
          <p>Import Document Intelligence Platform</p>

          <label>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
            required
          />

          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            required
          />

          {error && <p className="error-message">{error}</p>}

          <button className="primary-button" type="submit">
            Sign In
          </button>
        </form>
      </div>
    );
  }

  const needsReview = shipments.filter(
    (s) => s.status === "needs_review"
  ).length;

  const pending = shipments.filter(
    (s) => s.status === "pending_documents"
  ).length;

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">C</div>
          <div>
            <h2>CargoLens</h2>
            <span>AI DOCUMENT INTELLIGENCE</span>
          </div>
        </div>

        <p className="menu-label">WORKSPACE</p>

        {[
          "Dashboard",
          "Shipments",
          "Create Shipment",
          "Document Review",
          "Audit History",
        ].map((page) => (
          <button
            key={page}
            className={`nav-item ${activePage === page ? "active" : ""}`}
            onClick={() => {
              setActivePage(page);
              setError("");
            }}
          >
            {page}
          </button>
        ))}

        <div className="sidebar-bottom">
          <div className="user-avatar">
            {user.email?.slice(0, 1).toUpperCase()}
          </div>
          <div>
            <strong>{user.email}</strong>
            <span>{user.role}</span>
            <button className="logout-button" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <span className="breadcrumb">Workspace / {activePage}</span>
            <h1>{activePage}</h1>
          </div>
          <span className="environment">LIVE BACKEND</span>
        </header>

        {error && <p className="error-message">{error}</p>}

        {activePage === "Dashboard" && (
          <>
            <section className="welcome">
              <div>
                <h2>Welcome to CargoLens AI</h2>
                <p>
                  Manage import documents and identify shipment inconsistencies.
                </p>
              </div>
              <button
                className="primary-button"
                onClick={() => setActivePage("Create Shipment")}
              >
                + New Shipment
              </button>
            </section>

            <section className="stats-grid">
              <StatCard title="Total Shipments" value={shipments.length} />
              <StatCard title="Needs Review" value={needsReview} />
              <StatCard title="Pending Documents" value={pending} />
              <StatCard
                title="Other Shipments"
                value={shipments.length - needsReview - pending}
              />
            </section>

            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h3>Recent Shipments</h3>
                  <p>Records loaded from your database</p>
                </div>
                <button className="secondary-button" onClick={loadShipments}>
                  Refresh
                </button>
              </div>
              {loading ? (
                <p>Loading shipments...</p>
              ) : (
                <ShipmentTable shipments={shipments.slice(0, 5)} />
              )}
            </section>
          </>
        )}

        {activePage === "Shipments" && (
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h3>All Shipments</h3>
                <p>Live shipment records</p>
              </div>
              <input
                className="search-input"
                placeholder="Search shipment or supplier..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <div className="shipment-form">
              <label>Select shipment to export</label>

              <select
                className="search-input"
                value={exportShipmentId}
                onChange={(e) => setExportShipmentId(e.target.value)}
              >
                <option value="">Choose a shipment</option>
                {shipments.map((shipment) => (
                  <option key={shipment.id} value={shipment.id}>
                    {shipment.shipment_number}
                  </option>
                ))}
              </select>

              <button
                className="primary-button"
                onClick={handleExportCsv}
                disabled={!exportShipmentId || exporting}
              >
                {exporting ? "Exporting..." : "Export CSV"}
              </button>
            </div>

            {loading ? (
              <p>Loading...</p>
            ) : (
              <ShipmentTable shipments={filteredShipments} />
            )}
          </section>
        )}

        {activePage === "Create Shipment" && (
          <section className="panel">
            <h3>Create New Shipment</h3>
            <form className="shipment-form" onSubmit={createShipment}>
              <label>Shipment Number</label>
              <input
                value={shipmentNumber}
                onChange={(e) => setShipmentNumber(e.target.value)}
                placeholder="Example: SHP-24813"
                required
              />

              <label>Supplier Name</label>
              <input
                value={supplier}
                onChange={(e) => setSupplier(e.target.value)}
                placeholder="Enter supplier name"
                required
              />

              <label>Origin Country</label>
              <input
                value={origin}
                onChange={(e) => setOrigin(e.target.value)}
                placeholder="Example: China"
                required
              />

              <button className="primary-button" type="submit">
                Create Shipment
              </button>
            </form>
          </section>
        )}

        {activePage === "Document Review" && (
          <DocumentReview
            shipments={shipments}
            apiRequest={apiRequest}
          />
        )}

        {activePage === "Audit History" && (
          <AuditHistory
            shipments={shipments}
            apiRequest={apiRequest}
          />
        )}
      </main>
    </div>
  );
}

function StatCard({ title, value }) {
  return (
    <div className="stat-card">
      <span>{title}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ShipmentTable({ shipments }) {
  if (!shipments.length) return <p>No shipments found.</p>;

  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>SHIPMENT ID</th>
            <th>SUPPLIER</th>
            <th>ORIGIN</th>
            <th>STATUS</th>
          </tr>
        </thead>
        <tbody>
          {shipments.map((shipment) => (
            <tr key={shipment.id}>
              <td className="shipment-number">{shipment.shipment_number}</td>
              <td>{shipment.supplier_name}</td>
              <td>{shipment.origin_country}</td>
              <td>
                <span className="status">
                  {shipment.status.replaceAll("_", " ")}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DocumentReview({ shipments, apiRequest }) {
  const [shipmentId, setShipmentId] = useState("");
  const [documentType, setDocumentType] = useState("invoice");
  const [file, setFile] = useState(null);
  const [extractions, setExtractions] = useState(null);
  const [validation, setValidation] = useState(null);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingResults, setLoadingResults] = useState(false);
  const [deletingDocumentId, setDeletingDocumentId] = useState(null);

  async function loadResults(id) {
    if (!id) return;

    setLoadingResults(true);
    try {
      const extractionData = await apiRequest(
        `/shipments/${id}/extractions`
      );
      const validationData = await apiRequest(
        `/shipments/${id}/validation`
      );
      setExtractions(extractionData);
      setValidation(validationData);
    } catch (err) {
      setMessage(err.message);
      setMessageType("error");
    } finally {
      setLoadingResults(false);
    }
  }

  async function handleUpload(event) {
    event.preventDefault();

    if (!shipmentId) {
      setMessage("Please select a shipment first.");
      setMessageType("error");
      return;
    }

    if (!file) {
      setMessage("Please choose a PDF file to upload.");
      setMessageType("error");
      return;
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setMessage("Only PDF files are supported.");
      setMessageType("error");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setMessage("File size cannot exceed 10 MB.");
      setMessageType("error");
      return;
    }

    setLoading(true);
    setMessage("");
    setMessageType("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      await apiRequest(
        `/shipments/${shipmentId}/documents?document_type=${documentType}`,
        {
          method: "POST",
          body: formData,
        }
      );

      setMessage("Document uploaded successfully.");
      setMessageType("success");
      setFile(null);

      const fileInput = document.getElementById("doc-upload-input");
      if (fileInput) fileInput.value = "";

      await loadResults(shipmentId);
    } catch (err) {
      setMessage(err.message);
      setMessageType("error");
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(documentId, filename) {
    const confirmed = window.confirm(
      `Are you sure you want to delete ${filename}?`
    );

    if (!confirmed) return;

    setDeletingDocumentId(documentId);
    setMessage("");
    setMessageType("");

    try {
      await apiRequest(
        `/shipments/${shipmentId}/documents/${documentId}`,
        { method: "DELETE" }
      );

      setMessage("Document deleted successfully.");
      setMessageType("success");

      await loadResults(shipmentId);
    } catch (err) {
      setMessage(err.message);
      setMessageType("error");
    } finally {
      setDeletingDocumentId(null);
    }
  }

  async function handleShipmentChange(id) {
    setShipmentId(id);
    setExtractions(null);
    setValidation(null);
    setMessage("");
    setMessageType("");

    if (id) {
      await loadResults(id);
    }
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h3>Document Review</h3>
          <p>Upload shipment documents and review AI extraction results.</p>
        </div>
        {shipmentId && (
          <button
            className="secondary-button"
            onClick={() => loadResults(shipmentId)}
            disabled={loadingResults}
          >
            {loadingResults ? "Refreshing..." : "Refresh"}
          </button>
        )}
      </div>

      <div className="shipment-form">
        <label>Select Shipment</label>
        <select
          className="search-input"
          value={shipmentId}
          onChange={(e) => handleShipmentChange(e.target.value)}
        >
          <option value="">Choose a shipment</option>
          {shipments.map((shipment) => (
            <option key={shipment.id} value={shipment.id}>
              {shipment.shipment_number} — {shipment.supplier_name}
            </option>
          ))}
        </select>
      </div>

      {shipmentId && (
        <form className="shipment-form" onSubmit={handleUpload}>
          <label>Document Type</label>
          <select
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value)}
          >
            <option value="invoice">Invoice</option>
            <option value="packing_list">Packing List</option>
            <option value="bill_of_lading">Bill of Lading</option>
          </select>

          <label>Upload PDF (max 10 MB)</label>
          <input
            id="doc-upload-input"
            type="file"
            accept=".pdf,application/pdf"
            onChange={(e) => setFile(e.target.files[0] || null)}
          />

          <button
            className="primary-button"
            type="submit"
            disabled={loading || !file}
          >
            {loading ? "Uploading..." : "Upload Document"}
          </button>
        </form>
      )}

      {message && (
        <p className={messageType === "error" ? "error-message" : ""}>
          {message}
        </p>
      )}

      {!shipmentId && (
        <p className="empty-state">
          Select a shipment to view extracted information and validation results.
        </p>
      )}

      {shipmentId && loadingResults && (
        <p>Loading extraction and validation results...</p>
      )}

      {shipmentId && !loadingResults && extractions && (
        <div className="panel">
          <h3>Extracted Information</h3>
          <p>Documents processed: {extractions.total_documents}</p>

          {extractions.total_documents === 0 && (
            <p className="empty-state">
              No documents uploaded yet for this shipment.
            </p>
          )}

          {extractions.documents.map((doc) => (
            <div key={doc.document_id} className="extraction-block">
              <div className="panel-heading">
                <h4>
                  {doc.document_type.replaceAll("_", " ").toUpperCase()}
                </h4>

                <button
                  className="secondary-button"
                  onClick={() =>
                    handleDelete(doc.document_id, doc.filename)
                  }
                  disabled={deletingDocumentId !== null || loadingResults}
                >
                  {deletingDocumentId === doc.document_id
                    ? "Deleting..."
                    : "Delete"}
                </button>
              </div>

              <p className="muted">File: {doc.filename}</p>

              {doc.extraction?.fields ? (
                <div className="table-wrapper">
                  <table>
                    <thead>
                      <tr>
                        <th>FIELD</th>
                        <th>EXTRACTED VALUE</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(doc.extraction.fields).map(
                        ([key, value]) => (
                          <tr key={key}>
                            <td>{key.replaceAll("_", " ")}</td>
                            <td>
                              {value === null || value === ""
                                ? "Not available"
                                : String(value)}
                            </td>
                          </tr>
                        )
                      )}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="empty-state">
                  No structured fields were extracted from this document.
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {shipmentId && !loadingResults && validation && (
        <div className="panel">
          <h3>Validation Results</h3>

          {validation.checks?.length ? (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>CHECK</th>
                    <th>STATUS</th>
                    <th>DETAILS</th>
                  </tr>
                </thead>
                <tbody>
                  {validation.checks.map((check, index) => (
                    <tr key={index}>
                      <td>{check.label}</td>
                      <td>
                        <span
                          className={`status ${
                            check.status === "fail" ? "status-fail" : ""
                          }`}
                        >
                          {check.status}
                        </span>
                      </td>
                      <td>
                        {check.message ||
                          (check.values
                            ? check.values
                                .map(
                                  (v) =>
                                    `${v.document_type}: ${v.value}`
                                )
                                .join(" | ")
                            : "—")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="empty-state">
              No cross-check results available. Upload all three document
              types to run full validation.
            </p>
          )}
        </div>
      )}
    </section>
  );
}

function AuditHistory({ shipments, apiRequest }) {
  const [logs, setLogs] = useState([]);
  const [selectedShipment, setSelectedShipment] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadLogs(shipmentId) {
    if (!shipmentId) {
      setLogs([]);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const data = await apiRequest(
        `/shipments/${shipmentId}/audit-logs`
      );
      setLogs(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (selectedShipment) loadLogs(selectedShipment);
  }, [selectedShipment]);

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h3>Shipment Audit History</h3>
          <p>Track shipment creation, uploads and status changes.</p>
        </div>
        <select
          className="search-input"
          value={selectedShipment}
          onChange={(e) => setSelectedShipment(e.target.value)}
        >
          <option value="">Select a shipment</option>
          {shipments.map((shipment) => (
            <option key={shipment.id} value={shipment.id}>
              {shipment.shipment_number}
            </option>
          ))}
        </select>
      </div>

      {error && <p className="error-message">{error}</p>}
      {loading && <p>Loading audit history...</p>}

      {!loading && selectedShipment && logs.length === 0 && (
        <p className="empty-state">
          No audit activities found for this shipment.
        </p>
      )}

      {!selectedShipment && (
        <p className="empty-state">
          Select a shipment to view its activity.
        </p>
      )}

      {logs.length > 0 && (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>ACTION</th>
                <th>DETAILS</th>
                <th>USER ID</th>
                <th>DATE</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{log.action.replaceAll("_", " ")}</td>
                  <td>{log.details}</td>
                  <td>{log.user_id}</td>
                  <td>{new Date(log.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}