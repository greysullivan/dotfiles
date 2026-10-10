local M = {}
local uv = vim.uv
local picker = require("minimal.picker")
M.root = vim.fs.normalize(vim.fn.expand("~/Notes"))
local stamps, pending, reserved = {}, {}, {}

local function stamp(path)
  local stat = uv.fs_stat(path)
  if not stat then return false end
  return table.concat({ stat.dev, stat.ino, stat.size, stat.mtime.sec, stat.mtime.nsec }, ":")
end

function M.is_path(path)
  if path == "" or not path:match("%.md$") then return false end
  local root = uv.fs_realpath(M.root) or M.root
  local resolved = uv.fs_realpath(path)
    or ((uv.fs_realpath(vim.fn.fnamemodify(path, ":h")) or vim.fn.fnamemodify(path, ":h")) .. "/" .. vim.fn.fnamemodify(path, ":t"))
  return resolved:sub(1, #root + 1) == root .. "/"
end

local function meaningful(buf)
  for _, line in ipairs(vim.api.nvim_buf_get_lines(buf, 0, -1, false)) do
    if line:find("%S") then return true end
  end
  return false
end

local function new_path(stem)
  vim.fn.mkdir(M.root, "p", 448)
  local prefix = (stem and (stem .. "-") or "") .. os.date("%Y%m%d-%H%M%S")
  for i = 0, 9999 do
    local path = M.root .. "/" .. prefix .. (i == 0 and "" or "-" .. i) .. ".md"
    -- Reserve the filename exclusively; concurrent editors cannot collide.
    local fd = uv.fs_open(path, "wx", 384)
    if fd then uv.fs_close(fd); return path end
    if not uv.fs_stat(path) then error("Cannot create a note in " .. M.root) end
  end
  error("Cannot allocate a unique note filename")
end

function M.save(buf)
  buf = buf or vim.api.nvim_get_current_buf()
  if not vim.api.nvim_buf_is_valid(buf) or not vim.b[buf].minimal_note or not vim.bo[buf].modified then return true end
  local ok, err = pcall(function()
    local path = vim.api.nvim_buf_get_name(buf)
    if path == "" then
      if not meaningful(buf) then return end
      path = new_path()
      vim.api.nvim_buf_set_name(buf, path)
      stamps[buf] = stamp(path)
      reserved[buf] = true
    end
    if not M.is_path(path) then error("Note is outside ~/Notes; use :write explicitly") end
    if stamps[buf] ~= stamp(path) then error("Note changed on disk; autosave stopped: " .. path) end
    if vim.bo[buf].readonly then error("Note is read-only: " .. path) end
    vim.api.nvim_buf_call(buf, function() vim.cmd(reserved[buf] and "silent write!" or "silent write") end)
  end)
  if not ok then
    -- Suppress repeated timer errors, while explicit attempts remain visible.
    if vim.b[buf].minimal_save_error ~= tostring(err) then picker.error(tostring(err)) end
    vim.b[buf].minimal_save_error = tostring(err)
  else vim.b[buf].minimal_save_error = nil end
  return ok
end

local function list_item(line)
  local indent, marker, body = line:match("^(%s*)([-+*])%s+(.*)$")
  if not marker then indent, marker, body = line:match("^(%s*)(%d+[.)])%s+(.*)$") end
  if not marker then return end
  local box = body:match("^%[[ xX]%]%s*")
  return { indent = indent, marker = marker, body = box and body:sub(#box + 1) or body, box = box ~= nil }
end

function M.indent(direction, visual)
  local buf = vim.api.nvim_get_current_buf()
  local cursor = vim.api.nvim_win_get_cursor(0)
  local first, last = cursor[1], cursor[1]
  if visual then
    local anchor = vim.fn.getpos("v")[2]
    first, last = math.min(anchor, first), math.max(anchor, first)
  else
    local current = vim.api.nvim_buf_get_lines(buf, first - 1, first, false)[1]
    local item = list_item(current)
    if not item then return false end
    local lines = vim.api.nvim_buf_get_lines(buf, first, -1, false)
    for _, line in ipairs(lines) do
      if line:match("^%s*$") or #(line:match("^%s*") or "") <= #item.indent then break end
      last = last + 1
    end
  end
  local lines = vim.api.nvim_buf_get_lines(buf, first - 1, last, false)
  local delta = 0
  for i, line in ipairs(lines) do
    local before = #line
    if direction > 0 then lines[i] = "  " .. line
    else lines[i] = line:gsub("^  ", "", 1):gsub("^\t", "", 1) end
    if first + i - 1 == cursor[1] then delta = #lines[i] - before end
  end
  vim.api.nvim_buf_set_lines(buf, first - 1, last, false, lines)
  vim.api.nvim_win_set_cursor(0, { cursor[1], math.max(0, cursor[2] + delta) })
  return true
end

function M.enter()
  local cursor = vim.api.nvim_win_get_cursor(0)
  local line = vim.api.nvim_get_current_line()
  local item = list_item(line:sub(1, cursor[2]))
  if not item then return false end
  local suffix = line:sub(cursor[2] + 1)
  if item.body:match("^%s*$") and suffix:match("^%s*$") then
    vim.api.nvim_set_current_line(item.indent)
    vim.api.nvim_win_set_cursor(0, { cursor[1], #item.indent })
    return true
  end
  local number, punctuation = item.marker:match("^(%d+)([.)])$")
  local marker = number and (tonumber(number) + 1) .. punctuation or item.marker
  local prefix = item.indent .. marker .. " " .. (item.box and "[ ] " or "")
  vim.api.nvim_buf_set_lines(0, cursor[1] - 1, cursor[1], false, { line:sub(1, cursor[2]), prefix .. suffix })
  vim.api.nvim_win_set_cursor(0, { cursor[1] + 1, #prefix })
  return true
end

function M.new()
  if not M.save() then return end
  local buf = vim.api.nvim_create_buf(true, false)
  vim.api.nvim_set_current_buf(buf)
  vim.bo[buf].filetype = "markdown"
  M.attach(buf)
  vim.cmd.startinsert()
end

function M.pool()
  if not M.save() then return end
  if vim.fn.isdirectory(M.root) == 0 then vim.notify("No notes yet"); return end
  local out, code, err = picker.run({ "rg", "--files", "--hidden", "-g", "*.md", "-g", "!.git", "-0", "." }, M.root)
  if code > 1 then picker.error(err); return end
  local items = {}
  for relative in out:gmatch("([^%z]+)%z") do
    relative = relative:gsub("^%./", "")
    local path = M.root .. "/" .. relative
    if M.is_path(path) then
      local title = ""
      local file = io.open(path, "r")
      if file then
        for _ = 1, 20 do
          local line = file:read("*l")
          if not line then break end
          if line:find("%S") then title = line:gsub("^#+%s*", ""); break end
        end
        file:close()
      end
      items[#items + 1] = { label = relative .. (title ~= "" and "  " .. title or ""), path = path }
    end
  end
  table.sort(items, function(a, b) return a.path > b.path end)
  picker.choose(items, "note", function(item) picker.open(item.path) end)
end

function M.search()
  if not M.save() then return end
  if vim.fn.isdirectory(M.root) == 0 then vim.notify("No notes yet"); return end
  picker.search(M.root, "*.md")
end

function M.add()
  local source = vim.api.nvim_buf_get_name(0)
  if not source:match("%.md$") then picker.error("NotesAdd requires a Markdown file"); return end
  if M.is_path(source) then vim.notify("Already in the notes pool"); return end
  local lines = vim.api.nvim_buf_get_lines(0, 0, -1, false)
  local ok, err = pcall(function()
    local path = new_path(vim.fn.fnamemodify(source, ":t:r"))
    if vim.fn.writefile(lines, path) ~= 0 then error("Cannot write imported note") end
    picker.open(path)
  end)
  if not ok then picker.error(tostring(err)) end
end

function M.attach(buf)
  if vim.b[buf].minimal_note then return end
  vim.b[buf].minimal_note = true
  stamps[buf] = stamp(vim.api.nvim_buf_get_name(buf))
  vim.bo[buf].expandtab = true
  vim.bo[buf].shiftwidth = 2
  vim.bo[buf].softtabstop = 2
  vim.bo[buf].tabstop = 2
  vim.bo[buf].autoindent = false
  vim.bo[buf].indentexpr = ""
  vim.bo[buf].formatoptions = ""
  local map = function(mode, key, action, options)
    vim.keymap.set(mode, key, action, vim.tbl_extend("force", { buffer = buf }, options or {}))
  end
  local function feed(keys)
    vim.api.nvim_feedkeys(vim.api.nvim_replace_termcodes(keys, true, false, true), "ni", false)
  end
  map("i", "<Tab>", function() if not M.indent(1) then feed("  ") end end)
  map("i", "<S-Tab>", function() if not M.indent(-1) then feed("<C-d>") end end)
  map("x", "<Tab>", function() M.indent(1, true) end)
  map("x", "<S-Tab>", function() M.indent(-1, true) end)
  map("i", "<CR>", function() if not M.enter() then feed("<CR>") end end)
  for key, action in pairs({ ["<C-n>"] = M.new, ["<C-o>"] = M.pool, ["<C-f>"] = M.search,
    ["<C-s>"] = function() M.save(buf) end }) do map({ "i", "n" }, key, action) end
  map("i", "<C-z>", "<C-o>u")
  map("i", "<C-y>", "<C-o><C-r>")
  if vim.api.nvim_get_current_buf() == buf then
    vim.wo.wrap = true
    vim.wo.linebreak = true
    vim.wo.conceallevel = 0
  end
end

function M.setup()
  local group = vim.api.nvim_create_augroup("MinimalNotes", { clear = true })
  vim.api.nvim_create_autocmd({ "BufReadPost", "BufNewFile" }, { group = group, callback = function(event)
    if M.is_path(vim.api.nvim_buf_get_name(event.buf)) then M.attach(event.buf) end
  end })
  vim.api.nvim_create_autocmd({ "BufEnter", "WinEnter" }, { group = group, callback = function(event)
    local note = vim.b[event.buf].minimal_note == true
    vim.wo.wrap = note
    vim.wo.linebreak = note
    vim.wo.conceallevel = 0
    if note then
      vim.schedule(function()
        if vim.api.nvim_get_current_buf() == event.buf and vim.bo[event.buf].buftype == "" then vim.cmd.startinsert() end
      end)
    end
  end })
  vim.api.nvim_create_autocmd({ "TextChanged", "TextChangedI" }, { group = group, callback = function(event)
    if not vim.b[event.buf].minimal_note then return end
    pending[event.buf] = (pending[event.buf] or 0) + 1
    local generation = pending[event.buf]
    vim.defer_fn(function()
      if pending[event.buf] == generation then M.save(event.buf) end
    end, 750)
  end })
  vim.api.nvim_create_autocmd({ "BufLeave", "FocusLost", "QuitPre" }, { group = group, callback = function(event)
    if not M.save(event.buf) and event.event == "QuitPre" then error("Note is unsaved; resolve the write error before quitting") end
  end })
  vim.api.nvim_create_autocmd("VimLeavePre", { group = group, callback = function()
    for _, buf in ipairs(vim.api.nvim_list_bufs()) do M.save(buf) end
  end })
  vim.api.nvim_create_autocmd({ "BufWritePost", "BufReadPost" }, { group = group, callback = function(event)
    if vim.b[event.buf].minimal_note then
      stamps[event.buf] = stamp(vim.api.nvim_buf_get_name(event.buf))
      reserved[event.buf] = nil
      vim.b[event.buf].minimal_save_error = nil
    end
  end })
  vim.api.nvim_create_autocmd("BufWipeout", { group = group, callback = function(event)
    stamps[event.buf], pending[event.buf], reserved[event.buf] = nil, nil, nil
  end })
  vim.api.nvim_create_autocmd("VimEnter", { group = group, callback = function()
    if vim.g.notes_launch == 1 then M.new() end
  end })
  for name, action in pairs({ NotesNew = M.new, NotesPool = M.pool, NotesSearch = M.search, NotesAdd = M.add }) do
    vim.api.nvim_create_user_command(name, action, {})
  end
  for key, action in pairs({ nn = M.new, np = M.pool, ns = M.search, na = M.add }) do
    vim.keymap.set("n", "<leader>" .. key, action)
  end
end

return M
