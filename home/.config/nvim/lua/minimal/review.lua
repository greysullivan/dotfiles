local M = {}
local picker = require("minimal.picker")

local function header_path(text, prefix)
  text = text:sub(5)
  if text:sub(1, 1) == '"' then
    text = text:match('^"(.*)"') or text
    local escapes = { a = "\a", b = "\b", t = "\t", n = "\n", v = "\v", f = "\f", r = "\r" }
    text = text:gsub("\\([0-7][0-7][0-7])", function(octal) return string.char(tonumber(octal, 8)) end)
      :gsub("\\(.)", function(char) return escapes[char] or char end)
  else
    text = text:gsub("\t$", "")
  end
  return text:gsub("^" .. prefix .. "/", "")
end

function M.open(staged)
  local root = picker.root()
  local args = { "git", "-c", "core.quotePath=false", "diff", "--no-ext-diff", "--no-textconv", "--no-color", "--no-renames",
    "--src-prefix=a/", "--dst-prefix=b/" }
  if staged then args[#args + 1] = "--cached" end
  local out, code, err = picker.run(args, root)
  if code ~= 0 then picker.error(vim.trim(err)); return end
  if out == "" then vim.notify("No " .. (staged and "staged" or "working-tree") .. " changes"); return end
  local origin = vim.api.nvim_get_current_buf()
  local buf = vim.api.nvim_create_buf(false, true)
  local lines = vim.split(out:gsub("\n$", ""), "\n", { plain = true })
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, lines)
  vim.bo[buf].filetype = "diff"
  vim.bo[buf].bufhidden = "wipe"
  vim.bo[buf].modifiable = false
  vim.api.nvim_set_current_buf(buf)
  local locations, path, oldpath, newpath, oldline, newline = {}, nil, nil, nil, nil, nil
  for i, text in ipairs(lines) do
    if text:match("^diff %-%-git ") then
      path, oldpath, newpath, oldline, newline = nil, nil, nil, nil, nil
    elseif not oldline and text:match("^%-%-%- ") then oldpath = header_path(text, "a")
    elseif not oldline and text:match("^%+%+%+ ") then
      newpath = header_path(text, "b")
      path = newpath ~= "/dev/null" and newpath or oldpath
    elseif text:match("^@@ ") then
      oldline, newline = text:match("^@@ %-(%d+)[^ ]* %+(%d+)")
      oldline, newline = tonumber(oldline), tonumber(newline)
      if path then locations[i] = { path = path, line = newpath == "/dev/null" and oldline or newline } end
    elseif path and newline then
      locations[i] = { path = path, line = newpath == "/dev/null" and oldline or newline }
      local marker = text:sub(1, 1)
      if marker ~= "-" and marker ~= "\\" then newline = newline + 1 end
      if marker ~= "+" and marker ~= "\\" then oldline = oldline + 1 end
    end
  end
  vim.keymap.set("n", "<CR>", function()
    local location = locations[vim.api.nvim_win_get_cursor(0)[1]]
    if not location then return end
    local target = root .. "/" .. location.path
    if vim.fn.filereadable(target) == 0 then vim.notify("File is absent from the working tree: " .. location.path); return end
    picker.open(target, location.line)
  end, { buffer = buf })
  vim.keymap.set("n", "q", function()
    if vim.api.nvim_buf_is_valid(origin) then vim.api.nvim_set_current_buf(origin)
    else vim.cmd.enew() end
  end, { buffer = buf })
end

function M.setup()
  vim.keymap.set("n", "<leader>gr", function() M.open(false) end)
  vim.keymap.set("n", "<leader>gs", function() M.open(true) end)
  vim.api.nvim_create_user_command("Review", function(opts) M.open(opts.args == "staged") end,
    { nargs = "?", complete = function() return { "working", "staged" } end })
end

return M
