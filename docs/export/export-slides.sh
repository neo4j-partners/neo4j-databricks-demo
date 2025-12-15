#!/bin/bash
#
# export-slides.sh
# Exports Marp markdown slides to PDF format
#
# This script:
# 1. Finds all slide markdown files in the slides directory
# 2. Converts each to PDF using Marp CLI
# 3. Optionally creates a combined all-slides PDF
#
# Requirements:
# - marp-cli (npm install -g @marp-team/marp-cli)
# - macOS (uses built-in PDF join utility for --combined)
#
# Usage:
#   ./export-slides.sh              # Export all slides
#   ./export-slides.sh --slide 01   # Export only slide starting with 01-
#   ./export-slides.sh --combined   # Also create combined PDF of all slides
#   ./export-slides.sh --clean      # Clean up all generated PDFs
#

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SLIDES_DIR="$PROJECT_ROOT/slides"
EXPORT_DIR="$SCRIPT_DIR"
TEMP_DIR="$EXPORT_DIR/.temp"

# macOS PDF join utility
PDF_JOIN="/System/Library/Automator/Combine PDF Pages.action/Contents/MacOS/join"

# =============================================================================
# Color Output
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
log_step()    { echo -e "${CYAN}[STEP]${NC} $1"; }

# =============================================================================
# Help
# =============================================================================

show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Export Marp markdown slides to PDF format.

Options:
    -h, --help          Show this help message
    -s, --slide PREFIX  Export only slides starting with PREFIX (e.g., --slide 01)
    -c, --combined      Create a combined PDF of all slides
    --clean             Remove all generated PDFs and temp files
    --keep-temp         Keep intermediate PDF files (for debugging)
    --scale FACTOR      Image scale factor for PDF (default: 2)

Examples:
    $(basename "$0")                    # Export all slides
    $(basename "$0") --slide 01         # Export only 01-* slides
    $(basename "$0") --slide lab1       # Export only *lab1* slides
    $(basename "$0") --combined         # Export all + combined PDF
    $(basename "$0") --clean            # Clean up all PDFs

EOF
}

# =============================================================================
# Dependency Checks
# =============================================================================

check_dependencies() {
    log_step "Checking dependencies..."

    local missing=0

    # Check for marp
    if ! command -v marp &> /dev/null; then
        log_error "marp-cli is not installed"
        log_info "Install with: npm install -g @marp-team/marp-cli"
        missing=1
    else
        log_success "marp-cli found: $(marp --version)"
    fi

    if [[ $missing -eq 1 ]]; then
        exit 1
    fi
}

check_pdf_join() {
    # Only check for PDF join if combining
    if [[ ! -x "$PDF_JOIN" ]]; then
        log_warn "macOS PDF join utility not found - --combined may not work"
        return 1
    fi
    return 0
}

# =============================================================================
# Cleanup Functions
# =============================================================================

cleanup_temp() {
    if [[ -d "$TEMP_DIR" ]]; then
        rm -rf "$TEMP_DIR"
        log_info "Cleaned up temp directory"
    fi
}

cleanup_all() {
    log_step "Cleaning up all generated files..."

    # Remove temp directory
    cleanup_temp

    # Remove generated PDFs
    find "$EXPORT_DIR" -name "*.pdf" -type f -delete 2>/dev/null || true

    log_success "All generated files removed"
}

# =============================================================================
# Export Functions
# =============================================================================

# Convert a single markdown file to PDF
convert_to_pdf() {
    local input_file="$1"
    local output_file="$2"
    local scale="${3:-2}"

    log_info "Converting: $(basename "$input_file")"

    # Run marp with allow-local-files for image access
    if ! marp --pdf \
              --allow-local-files \
              --pdf-notes \
              --image-scale "$scale" \
              "$input_file" \
              -o "$output_file" 2>&1; then
        log_error "Failed to convert: $input_file"
        return 1
    fi

    return 0
}

# Merge multiple PDFs into one
merge_pdfs() {
    local output_file="$1"
    shift
    local -a input_files=("$@")

    if [[ ${#input_files[@]} -eq 0 ]]; then
        log_warn "No PDFs to merge"
        return 1
    fi

    if [[ ${#input_files[@]} -eq 1 ]]; then
        # Only one file, just copy it
        cp "${input_files[0]}" "$output_file"
        return 0
    fi

    log_info "Merging ${#input_files[@]} PDFs into: $(basename "$output_file")"

    if ! "$PDF_JOIN" -o "$output_file" "${input_files[@]}" 2>&1; then
        log_error "Failed to merge PDFs"
        return 1
    fi

    return 0
}

# Export all slides
export_all_slides() {
    local scale="$1"
    local keep_temp="$2"
    local create_combined="$3"
    local filter="${4:-}"

    log_step "Finding slide files..."

    # Find all slide files (bash 3.2 compatible)
    local -a slide_files=()
    while IFS= read -r file; do
        [[ -n "$file" ]] && slide_files+=("$file")
    done < <(find "$SLIDES_DIR" -maxdepth 1 -name "*-slides.md" -type f | sort)

    if [[ ${#slide_files[@]} -eq 0 ]]; then
        log_error "No slide files found in: $SLIDES_DIR"
        exit 1
    fi

    # Filter if specified
    if [[ -n "$filter" ]]; then
        local -a filtered_files=()
        for f in "${slide_files[@]}"; do
            if [[ "$(basename "$f")" == *"$filter"* ]]; then
                filtered_files+=("$f")
            fi
        done
        slide_files=("${filtered_files[@]}")

        if [[ ${#slide_files[@]} -eq 0 ]]; then
            log_error "No slide files matching '$filter' found"
            exit 1
        fi
    fi

    log_info "Found ${#slide_files[@]} slide file(s)"

    # Create temp directory for combined PDF
    if [[ "$create_combined" == "true" ]]; then
        mkdir -p "$TEMP_DIR"
    fi

    # Convert each slide file to PDF
    local -a pdf_files=()
    local failed=0

    for slide_file in "${slide_files[@]}"; do
        local base
        base="$(basename "$slide_file" .md)"
        local pdf_file="$EXPORT_DIR/${base}.pdf"
        local temp_pdf="$TEMP_DIR/${base}.pdf"

        if convert_to_pdf "$slide_file" "$pdf_file" "$scale"; then
            log_success "Created: ${base}.pdf"
            if [[ "$create_combined" == "true" ]]; then
                # Copy to temp for merging
                cp "$pdf_file" "$temp_pdf"
                pdf_files+=("$temp_pdf")
            fi
        else
            failed=$((failed + 1))
        fi
        echo ""
    done

    if [[ $failed -gt 0 ]]; then
        log_warn "$failed file(s) failed to convert"
    fi

    # Create combined PDF if requested
    if [[ "$create_combined" == "true" && ${#pdf_files[@]} -gt 0 ]]; then
        if check_pdf_join; then
            log_step "Creating combined PDF..."
            local combined_pdf="$EXPORT_DIR/all-slides-combined.pdf"
            if merge_pdfs "$combined_pdf" "${pdf_files[@]}"; then
                log_success "Created: all-slides-combined.pdf"
            fi
        else
            log_warn "Skipping combined PDF (macOS PDF join not available)"
        fi
    fi

    # Final cleanup
    if [[ "$keep_temp" != "true" ]]; then
        cleanup_temp
    fi
}

# =============================================================================
# Main
# =============================================================================

main() {
    local slide_filter=""
    local create_combined="false"
    local do_clean="false"
    local keep_temp="false"
    local scale="2"

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                exit 0
                ;;
            -s|--slide)
                slide_filter="$2"
                shift 2
                ;;
            -c|--combined)
                create_combined="true"
                shift
                ;;
            --clean)
                do_clean="true"
                shift
                ;;
            --keep-temp)
                keep_temp="true"
                shift
                ;;
            --scale)
                scale="$2"
                shift 2
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    echo ""
    echo "========================================"
    echo "     Marp Slides PDF Exporter          "
    echo "     Neo4j + Databricks Demo           "
    echo "========================================"
    echo ""

    # Handle clean
    if [[ "$do_clean" == "true" ]]; then
        cleanup_all
        exit 0
    fi

    # Check dependencies
    check_dependencies
    echo ""

    # Export
    export_all_slides "$scale" "$keep_temp" "$create_combined" "$slide_filter"

    echo ""
    log_success "Export complete!"
    echo ""
    log_info "Output directory: $EXPORT_DIR"
    ls -lh "$EXPORT_DIR"/*.pdf 2>/dev/null || log_warn "No PDFs found"
}

main "$@"
