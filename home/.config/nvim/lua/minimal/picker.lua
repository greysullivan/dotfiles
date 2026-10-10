local M = {}

function M.error(message)
  vim.notify(message, vim.log.levels.ERROR)
end

function M.run(argv, cwd)
  local result = vim.system(argv, { cwd = cwd, text = true }):wait()
  return result.stdout or "", result.code, result.stderr or ""
end

function M.root()
  local path = vim.api.nvim_buf_get_name(0)
  local cwd = path ~= "" and vim.fn.fnamemodify(path, ":h") or vim.fn.getcwd()
  local out, code = M.run({ "git", "rev-parse", "--show-toplevel" }, cwd)
  return code == 0 and vim.trim(out) or cwd
end

function M.open(path, line, col)
  vim.cmd.edit(vim.fn.fnameescape(path))
  if line then
    local count = vim.api.nvim_buf_line_count(0)
    line = math.max(1, math.min(line, count))
    local text = vim.api.nvim_buf_get_lines(0, line - 1, line, false)[1] or ""
    vim.api.nvim_win_set_cursor(0, { line, math.min(math.max(0, (col or 1) - 1), #text) })
  end
end

-- IDs keep filenames and search payloads out of shell commands and parsing.
function M.choose(items, prompt, callback)
  if #items == 0 then
    vim.notify("No matches")
    return
  end
  if vim.fn.executable("fzf") ~= 1 then
    M.error("fzf is unavailable")
    return
  end
  local input, output = vim.fn.tempname(), vim.fn.tempname()
  local records = {}
  for i, item in ipairs(items) do
    records[i] = i .. "\t" .. item.label:gsub("[\r\n\t]", " ")
  end
  vim.fn.writefile(records, input)
  vim.fn.setfperm(input, "rw-------")
  local origin = vim.api.nvim_get_current_win()
  local buf = vim.api.nvim_create_buf(false, true)
  local win = vim.api.nvim_open_win(buf, true, {
    relative = "editor", row = 0, col = 0,
    width = vim.o.columns, height = math.max(1, vim.o.lines - 1), style = "minimal", border = "none",
  })
  vim.bo[buf].bufhidden = "wipe"
  local cancelled = false
  local args = { "fzf", "--no-multi", "--layout=reverse", "--border=none", "--info=hidden", "--no-separator",
    "--pointer=", "--marker=", "--scrollbar=",
    "--delimiter=\t", "--with-nth=2..", "--prompt=" .. prompt .. " ",
    "--color=fg:#FFFFFF,bg:#000000,hl:#D0D0D0,fg+:#000000,bg+:#DFA0A0,hl+:#000000,prompt:#DFA0A0,pointer:#DFA0A0,marker:#DFA0A0",
  }
  if vim.env.TERM == "linux" then args[#args] = "--no-color" end
  local quoted = {}
  for _, arg in ipairs(args) do quoted[#quoted + 1] = vim.fn.shellescape(arg) end
  local shell = "exec " .. table.concat(quoted, " ") .. " < " .. vim.fn.shellescape(input) .. " > " .. vim.fn.shellescape(output)
  local function cleanup(code)
    local selected = vim.fn.filereadable(output) == 1 and vim.fn.readfile(output) or {}
    vim.fn.delete(input)
    vim.fn.delete(output)
    vim.cmd.stopinsert()
    if vim.api.nvim_win_is_valid(win) then vim.api.nvim_win_close(win, true) end
    if vim.api.nvim_win_is_valid(origin) then vim.api.nvim_set_current_win(origin) end
    local id = tonumber((selected[1] or ""):match("^(%d+)\t"))
    if code == 0 and id and items[id] then callback(items[id])
    elseif not cancelled and code ~= 0 and code ~= 1 and code ~= 130 and code ~= 143 then M.error("Search picker failed (" .. code .. ")") end
    local current = vim.api.nvim_get_current_buf()
    -- Let terminal-mode teardown finish before resuming note insertion.
    vim.defer_fn(function()
      if vim.api.nvim_get_current_buf() == current and vim.b[current].minimal_note then vim.cmd.startinsert() end
    end, 10)
  end
  local job = vim.fn.jobstart({ "sh", "-c", shell }, {
    term = true, on_exit = function(_, code) vim.schedule(function() cleanup(code) end) end,
  })
  if job <= 0 then cleanup(job); return end
  vim.keymap.set("t", "<Esc>", function() cancelled = true; vim.fn.jobstop(job) end, { buffer = buf })
  vim.cmd.startinsert()
end

function M.files()
  local root = M.root()
  local out, code, err = M.run({ "rg", "--files", "--hidden", "-g", "!.git", "-0" }, root)
  if code > 1 then M.error(err); return end
  local items = {}
  for path in out:gmatch("([^%z]+)%z") do items[#items + 1] = { label = path, path = root .. "/" .. path } end
  M.choose(items, "file", function(item) M.open(item.path) end)
end

function M.search(root, pattern)
  vim.ui.input({ prompt = "Search: " }, function(query)
    if not query or query == "" then return end
    local args = { "rg", "--json", "--hidden", "-g", "!.git" }
    if pattern then vim.list_extend(args, { "-g", pattern }) end
    vim.list_extend(args, { "--", query, "." })
    local out, code, err = M.run(args, root)
    if code > 1 then M.error(err); return end
    local items = {}
    for record in out:gmatch("[^\n]+") do
      local ok, event = pcall(vim.json.decode, record)
      if ok and event.type == "match" and event.data.path.text then
        local data = event.data
        local path = data.path.text:gsub("^%./", "")
        local col = data.submatches[1] and data.submatches[1].start + 1 or 1
        items[#items + 1] = { label = path .. ":" .. data.line_number .. "  " .. vim.trim(data.lines.text or ""),
          path = root .. "/" .. path, line = data.line_number, col = col }
      end
    end
    M.choose(items, "match", function(item) M.open(item.path, item.line, item.col) end)
  end)
end

function M.grep() M.search(M.root()) end

return M
