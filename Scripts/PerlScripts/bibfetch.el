;;; bibfetch.el -- Fetch BibTeX entries from Google Scholar

;; Author: Daniel Schoepe
;; Version: 0.1

;;; Commentary:

;; This programs uses the accompanying bibfetch.pl script to fetch
;; BibTeX entries from Google Scholar, and provides some convenience
;; functionality for inserting entries into a bibtex file. See
;; README.org for usage information.

;;; Code:

(require 'bibtex)

(defcustom bibfetch-script "bibfetch.pl"
  "Path to the bibfetch.pl script.")
(defcustom bibfetch-arguments nil
  "Arguments to pass to bibfetch.pl.")

(defvar bibfetch-original-buffer nil
  "Buffer from which bibtex was called.")
(make-variable-buffer-local 'bibfetch-original-buffer)

(defun bibfetch-next-entry ()
  "Skip to next entry."
  (interactive)
  (bibtex-end-of-entry)
  (forward-char)
  (bibtex-beginning-of-entry))

(defun bibfetch-previous-entry ()
  "Skip to previous entry."
  (interactive)
  (bibtex-beginning-of-entry)
  (backward-char)
  (bibtex-beginning-of-entry))

(defun bibfetch-copy-entry-as-kill ()
  "Copy current entry to killring."
  (interactive)
  (save-excursion
    (bibtex-mark-entry)
    (copy-region-as-kill (region-beginning) (region-end))))

(defun bibfetch-append-entry-to-caller ()
  "Append the current entry in the buffer in which bibfetch was called."
  (interactive)
  (if (not (buffer-live-p bibfetch-original-buffer))
      (message "Original buffer no longer exists")
    (bibfetch-copy-entry-as-kill)
    (with-current-buffer bibfetch-original-buffer
      (save-excursion
	(goto-char (point-max))
	(unless (bolp)
	  (newline))
	(insert (current-kill 0) "\n")))))

(defun bibfetch-quit ()
  "Exit bibfetch results"
  (kill-buffer-and-window))

(defvar bibfetch-mode-map
  (let ((map (make-sparse-keymap)))
    (set-keymap-parent map bibtex-mode-map)
    (define-key map "j" #'bibfetch-next-entry)
    (define-key map "k" #'bibfetch-previous-entry)
    (define-key map "y" #'bibfetch-copy-entry-as-kill)
    (define-key map "q" #'bibfetch-quit)
    (define-key map (kbd "<down>") #'bibfetch-next-entry)
    (define-key map (kbd "<up>") #'bibfetch-previous-entry)
    (define-key map (kbd "<return>") #'bibfetch-append-entry-to-caller)
    map)
  "Key map for interacting with bibfetch results")

(define-derived-mode bibfetch-mode bibtex-mode "bibfetch results"
  (use-local-map bibfetch-mode-map)
  (setq buffer-read-only t))

(defun bibfetch (query)
  "Query Google Scholar with QUERY and return results"
  (interactive "MQuery: ")
  (let ((buf (generate-new-buffer (concat "*bibfetch: " query "*")))
	(orig-buf (current-buffer)))
    (with-current-buffer buf
      ;; XXX make this asynchronous
      (apply #'call-process bibfetch-script nil t nil query bibfetch-arguments)
      (beginning-of-buffer)
      (bibfetch-mode)
      (setq bibfetch-original-buffer orig-buf)
      (switch-to-buffer-other-window buf))))

(provide 'bibfetch)
