"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { ref, onValue, off, push, set, remove } from "firebase/database";
import { database } from "@/lib/firebase";
import { useRouter } from "next/navigation";

interface Conversation {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: number;
}

interface SidebarProps {
  currentConversationId: string | null;
  onConversationSelect: (conversationId: string) => void;
  onNewChat: () => void;
}

export default function Sidebar({ currentConversationId, onConversationSelect, onNewChat }: SidebarProps) {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showThemeMenu, setShowThemeMenu] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark" | "system">("system");
  const [searchQuery, setSearchQuery] = useState("");
  const [editingConversationId, setEditingConversationId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [displayName, setDisplayName] = useState<string>("");

  // Apply theme function - defined before useEffects
  const applyTheme = (themeValue: "light" | "dark" | "system") => {
    console.log("Applying theme:", themeValue); // Debug log
    
    const htmlElement = document.documentElement;
    
    if (themeValue === "system") {
      const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      console.log("System preference:", isDark ? "dark" : "light"); // Debug log
      if (isDark) {
        htmlElement.classList.add("dark");
        htmlElement.setAttribute("data-theme", "dark");
      } else {
        htmlElement.classList.remove("dark");
        htmlElement.setAttribute("data-theme", "light");
      }
    } else if (themeValue === "dark") {
      htmlElement.classList.add("dark");
      htmlElement.setAttribute("data-theme", "dark");
    } else {
      htmlElement.classList.remove("dark");
      htmlElement.setAttribute("data-theme", "light");
    }
    
    // Force a style recalculation
    void htmlElement.offsetHeight;
    
    console.log("HTML classes:", htmlElement.classList.toString()); // Debug log
    console.log("Data theme:", htmlElement.getAttribute("data-theme")); // Debug log
  };

  // Load theme preference from RTDB
  useEffect(() => {
    if (!user) return;

    const isAnonymous = user.isAnonymous;
    const themePath = isAnonymous
      ? `users/anonymous/${user.uid}/settings/theme`
      : `users/${user.uid}/settings/theme`;

    const themeRef = ref(database, themePath);
    onValue(themeRef, (snapshot) => {
      const savedTheme = snapshot.val() as "light" | "dark" | "system" | null;
      console.log("Loaded theme from RTDB:", savedTheme); // Debug log
      if (savedTheme) {
        setTheme(savedTheme);
        applyTheme(savedTheme);
      } else {
        // Default to system preference
        console.log("No saved theme, using system default"); // Debug log
        setTheme("system");
        applyTheme("system");
      }
    });

    return () => {
      off(themeRef);
    };
  }, [user]);

  // Apply theme whenever it changes
  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  // Load display name from RTDB
  useEffect(() => {
    if (!user) return;

    const isAnonymous = user.isAnonymous;
    const displayNamePath = isAnonymous
      ? `users/anonymous/${user.uid}/profile/displayName`
      : `users/${user.uid}/profile/displayName`;

    const displayNameRef = ref(database, displayNamePath);
    onValue(displayNameRef, (snapshot) => {
      const name = snapshot.val();
      if (name) {
        setDisplayName(name);
      }
    });

    return () => {
      off(displayNameRef);
    };
  }, [user]);

  useEffect(() => {
    if (!user) return;

    const isAnonymous = user.isAnonymous;
    const conversationsPath = isAnonymous
      ? `users/anonymous/${user.uid}/conversations`
      : `users/${user.uid}/conversations`;

    const conversationsRef = ref(database, conversationsPath);

    onValue(conversationsRef, (snapshot) => {
      const data = snapshot.val();
      if (data) {
        const convList: Conversation[] = Object.keys(data).map((key) => {
          const conv = data[key];
          const messages = conv.messages || {};
          const messagesList = Object.values(messages) as any[];
          const lastMsg = messagesList.sort((a, b) => b.timestamp - a.timestamp)[0];
          
          return {
            id: key,
            title: conv.title || "New Chat",
            lastMessage: lastMsg?.content || "",
            timestamp: lastMsg?.timestamp || 0,
          };
        });
        
        setConversations(convList.sort((a, b) => b.timestamp - a.timestamp));
      } else {
        setConversations([]);
      }
    });

    return () => {
      off(conversationsRef);
    };
  }, [user]);

  const handleDeleteConversation = async (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!user) return;

    const isAnonymous = user.isAnonymous;
    const conversationPath = isAnonymous
      ? `users/anonymous/${user.uid}/conversations/${conversationId}`
      : `users/${user.uid}/conversations/${conversationId}`;

    try {
      await remove(ref(database, conversationPath));
      if (currentConversationId === conversationId) {
        onNewChat();
      }
    } catch (error) {
      console.error("Error deleting conversation:", error);
    }
  };

  const handleRenameConversation = async (conversationId: string) => {
    if (!user || !editingTitle.trim()) return;

    const isAnonymous = user.isAnonymous;
    const conversationPath = isAnonymous
      ? `users/anonymous/${user.uid}/conversations/${conversationId}/title`
      : `users/${user.uid}/conversations/${conversationId}/title`;

    try {
      await set(ref(database, conversationPath), editingTitle.trim());
      setEditingConversationId(null);
      setEditingTitle("");
    } catch (error) {
      console.error("Error renaming conversation:", error);
    }
  };

  const startEditing = (conversationId: string, currentTitle: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingConversationId(conversationId);
    setEditingTitle(currentTitle);
  };

  const handleLogout = async () => {
    await logout();
    router.push("/auth/login");
  };

  const changeTheme = async (newTheme: "light" | "dark" | "system") => {
    if (!user) return;
    
    setShowThemeMenu(false);
    setTheme(newTheme);
    applyTheme(newTheme);

    // Save to RTDB
    const isAnonymous = user.isAnonymous;
    const themePath = isAnonymous
      ? `users/anonymous/${user.uid}/settings/theme`
      : `users/${user.uid}/settings/theme`;

    try {
      await set(ref(database, themePath), newTheme);
    } catch (error) {
      console.error("Error saving theme preference:", error);
    }
  };

  const getThemeLabel = () => {
    if (theme === "system") return "System";
    if (theme === "dark") return "Dark";
    return "Light";
  };

  const getUserInitials = () => {
    if (user?.isAnonymous) return "G";
    const email = user?.email || "";
    return email.charAt(0).toUpperCase();
  };

  return (
    <>
      {/* Sidebar */}
      <div
        className={`${
          isCollapsed ? "w-16" : "w-64"
        } bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col transition-all duration-300`}
      >
        {/* Header */}
        <div className="p-4 flex items-center justify-between">
          {!isCollapsed && (
            <button
              onClick={onNewChat}
              className="flex-1 flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors text-gray-900 dark:text-white text-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New chat
            </button>
          )}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className={`p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors ${
              isCollapsed ? "mx-auto" : "ml-2"
            }`}
          >
            <svg className="w-5 h-5 text-gray-700 dark:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d={isCollapsed ? "M4 6h16M4 12h16M4 18h16" : "M6 18L18 6M6 6l12 12"}
              />
            </svg>
          </button>
        </div>

        {/* Search Bar */}
        {!isCollapsed && (
          <div className="px-3 pb-2">
            <div className="relative">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white text-sm rounded-lg pl-10 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
              />
            </div>
          </div>
        )}

        {/* Conversations List */}
        {!isCollapsed && (
          <div className="flex-1 overflow-y-auto px-2">
            {conversations
              .filter((conv) => 
                conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                conv.lastMessage.toLowerCase().includes(searchQuery.toLowerCase())
              )
              .map((conv) => (
              <div
                key={conv.id}
                onClick={() => onConversationSelect(conv.id)}
                className={`group relative mb-1 rounded-lg transition-colors cursor-pointer ${
                  currentConversationId === conv.id
                    ? "bg-gray-200 dark:bg-gray-800"
                    : "hover:bg-gray-100 dark:hover:bg-gray-800"
                }`}
              >
                {editingConversationId === conv.id ? (
                  <div className="p-3" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="text"
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          handleRenameConversation(conv.id);
                        } else if (e.key === "Escape") {
                          setEditingConversationId(null);
                          setEditingTitle("");
                        }
                      }}
                      onBlur={() => handleRenameConversation(conv.id)}
                      autoFocus
                      className="w-full bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white text-sm rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-600"
                    />
                  </div>
                ) : (
                  <>
                    <div className="p-3 pr-20">
                      <h3 className="text-sm text-gray-900 dark:text-white font-medium truncate">
                        {conv.title}
                      </h3>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-1">
                        {conv.lastMessage}
                      </p>
                    </div>
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={(e) => startEditing(conv.id, conv.title, e)}
                        className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                        title="Rename"
                      >
                        <svg className="w-4 h-4 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button
                        onClick={(e) => handleDeleteConversation(conv.id, e)}
                        className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                        title="Delete"
                      >
                        <svg className="w-4 h-4 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Footer - User Profile */}
        <div className="border-t border-gray-200 dark:border-gray-800 p-2">
          {!isCollapsed ? (
            <div className="relative">
              <button
                onClick={() => setShowProfileMenu(!showProfileMenu)}
                className="w-full flex items-center gap-3 p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              >
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-semibold">
                  {getUserInitials()}
                </div>
                <div className="flex-1 text-left min-w-0">
                  <p className="text-sm text-gray-900 dark:text-white font-medium truncate">
                    {displayName || (user?.isAnonymous ? "Guest User" : user?.email)}
                  </p>
                </div>
                <svg className="w-4 h-4 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Profile Menu */}
              {showProfileMenu && (
                <div className="absolute bottom-full left-0 right-0 mb-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden z-20">
                  <button
                    onClick={() => {
                      setShowProfileMenu(false);
                      router.push("/account");
                    }}
                    className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left"
                  >
                    <svg className="w-5 h-5 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                      />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <span className="text-sm text-gray-900 dark:text-white">Account Settings</span>
                  </button>
                  
                  {/* Theme Option with Submenu */}
                  <div className="relative border-t border-gray-200 dark:border-gray-700">
                    <button
                      onClick={() => setShowThemeMenu(!showThemeMenu)}
                      className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left"
                    >
                      <svg className="w-5 h-5 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                        />
                      </svg>
                      <span className="text-sm text-gray-900 dark:text-white flex-1">Theme: {getThemeLabel()}</span>
                      <svg className="w-4 h-4 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                    
                    {/* Theme Submenu */}
                    {showThemeMenu && (
                      <div className="bg-gray-50 dark:bg-gray-700">
                        <button
                          onClick={() => changeTheme("light")}
                          className={`w-full flex items-center justify-between px-8 py-2 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors text-left ${
                            theme === "light" ? "bg-gray-100 dark:bg-gray-600" : ""
                          }`}
                        >
                          <span className="text-sm text-gray-900 dark:text-white">Light</span>
                          {theme === "light" && (
                            <svg className="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </button>
                        <button
                          onClick={() => changeTheme("dark")}
                          className={`w-full flex items-center justify-between px-8 py-2 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors text-left ${
                            theme === "dark" ? "bg-gray-100 dark:bg-gray-600" : ""
                          }`}
                        >
                          <span className="text-sm text-gray-900 dark:text-white">Dark</span>
                          {theme === "dark" && (
                            <svg className="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </button>
                        <button
                          onClick={() => changeTheme("system")}
                          className={`w-full flex items-center justify-between px-8 py-2 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors text-left ${
                            theme === "system" ? "bg-gray-100 dark:bg-gray-600" : ""
                          }`}
                        >
                          <span className="text-sm text-gray-900 dark:text-white">System</span>
                          {theme === "system" && (
                            <svg className="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                  
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left border-t border-gray-200 dark:border-gray-700"
                  >
                    <svg className="w-5 h-5 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                      />
                    </svg>
                    <span className="text-sm text-gray-900 dark:text-white">Log out</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <button
              onClick={() => setIsCollapsed(false)}
              className="w-full flex items-center justify-center p-2 hover:bg-gray-800 dark:hover:bg-gray-900 rounded-lg transition-colors"
            >
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-semibold">
                {getUserInitials()}
              </div>
            </button>
          )}
        </div>
      </div>

      {/* Close menu overlay */}
      {showProfileMenu && (
        <div
          className="fixed inset-0 z-10"
          onClick={() => setShowProfileMenu(false)}
        />
      )}
    </>
  );
}
