local M = {}

function M.setup()
  vim.g.mapleader = " "
  vim.opt.laststatus = 0
  vim.opt.showtabline = 0
  vim.opt.showmode = false
  vim.opt.showcmd = false
  vim.opt.ruler = false
  vim.opt.cmdheight = 0
  vim.opt.number = false
  vim.opt.relativenumber = false
  vim.opt.signcolumn = "no"
  vim.opt.foldcolumn = "0"
  vim.opt.cursorline = false
  vim.opt.cursorcolumn = false
  vim.opt.colorcolumn = ""
  vim.opt.winbar = ""
  vim.opt.wrap = false
  vim.opt.hidden = true
  vim.opt.undofile = true
  vim.opt.splitright = true
  vim.opt.splitbelow = true
  vim.opt.fillchars:append({ eob = " " })
  vim.opt.shortmess:append("I")
  vim.cmd("syntax enable")

  local function appearance()
    local tty = vim.env.TERM == "linux"
    vim.opt.termguicolors = not tty
    local function hl(name, attrs) vim.api.nvim_set_hl(0, name, attrs) end
    hl("NormalFloat", { fg = "#FFFFFF", bg = "#000000", ctermfg = 15, ctermbg = 0 })
    hl("EndOfBuffer", { fg = "#000000", ctermfg = 0 })
    hl("DiffAdd", { fg = "#FFFFFF", bg = "#191919", ctermfg = 15, ctermbg = 0 })
    hl("DiffDelete", { fg = "#A3A3A3", bg = "#191919", ctermfg = 8, ctermbg = 0 })
    hl("DiffChange", { fg = "#D0D0D0", bg = "#191919", ctermfg = 15, ctermbg = 0 })
    hl("DiffText", { fg = "#FFFFFF", bg = "#343434", ctermfg = 15, ctermbg = 8, bold = true })
    for _, name in ipairs({ "diffAdded", "diffRemoved", "diffChanged", "diffFile", "diffNewFile", "diffOldFile", "diffLine" }) do
      hl(name, { fg = name == "diffRemoved" and "#A3A3A3" or "#FFFFFF", ctermfg = name == "diffRemoved" and 8 or 15,
        bold = name == "diffFile" or name == "diffLine" })
    end
    for i = 1, 6 do
      hl("markdownH" .. i, { fg = "#FFFFFF", ctermfg = 15, bold = true })
    end
    for _, name in ipairs({ "markdownHeadingDelimiter", "markdownListMarker", "markdownOrderedListMarker", "markdownBlockquote" }) do
      hl(name, { fg = "#A3A3A3", ctermfg = 8 })
    end
    hl("Visual", { fg = "#000000", bg = "#DFA0A0", ctermfg = 0, ctermbg = tty and 15 or 7 })
    if tty then
      for _, name in ipairs({ "Search", "IncSearch", "CurSearch", "PmenuSel" }) do
        hl(name, { fg = "#000000", bg = "#DFA0A0", ctermfg = 0, ctermbg = 15, bold = true })
      end
    end
  end
  local group = vim.api.nvim_create_augroup("MinimalAppearance", { clear = true })
  vim.api.nvim_create_autocmd("ColorScheme", { group = group, callback = appearance })
  appearance()

  require("minimal.notes").setup()
  require("minimal.review").setup()
  local picker = require("minimal.picker")
  vim.keymap.set("n", "<leader>ff", picker.files, { desc = "Find file" })
  vim.keymap.set("n", "<leader>fg", picker.grep, { desc = "Search project" })
end

return M
