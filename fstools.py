import argparse
import logging
from colorama import Fore, init, Style
from freshservice import FreshServiceManager

logger = logging.getLogger(__name__)

def parse_arguments():
    """Configure and parse command line arguments"""
    parser = argparse.ArgumentParser(
        description=f"""{Fore.CYAN}Freshservice Asset Management Tool

This tool allows you to:
1. Get asset information and components
2. Search assets by user, department, or location
3. List departments and locations
4. Import asset IDs from Excel files

Component Types:
cpu: Processor
ram: Memory
hdd: Logical Drive
nic: Network Adapter

Information Options:
-d: Department names
-t: Asset type
-l: Location
-u: User information
-s: System OS
-n: Machine IP
-m: MAC address
-sn: Serial number
-desc: Asset description
-a: All asset data (includes all above except components)

Search Options:
-su: Search by user full name
-sd: Search by department name
-sl: Search by location name
-ld: List all departments
-ll: List all locations in hierarchy

Component Options:
-c: Specify component types to include
-dj: Disable RAM joining
-jc: Combine CPU and RAM info

File Options:
-ie: Import IDs from Excel
-o: Export results to file
-v: Show results in console""",
        epilog=f"""{Fore.YELLOW}Examples:
1. Get asset info: python fstools.py -i 143-150 -e 145,147 -a -o output.xlsx
2. Get components: python fstools.py -i 143-150 -c cpu ram -o output.xlsx
3. Search by user: python fstools.py -su "John Doe" -o user_assets.xlsx
4. List locations: python fstools.py -ll
5. Import from Excel: python fstools.py -ie assets.xlsx"""
    )
    
    parser.add_argument('-i', '--ids',
                      help='Asset IDs (comma-separated or file path)')
    parser.add_argument('-e', '--exclude',
                      help='IDs to exclude (comma-separated)')
    parser.add_argument('-c', '--components', nargs='+',
                      choices=['cpu', 'ram', 'hdd', 'nic'],
                      help='Component types to include (space-separated). Valid options: cpu ram hdd nic')
    parser.add_argument('-o', '--output',
                      help='Output Excel file path')
    parser.add_argument('-v', '--verbose',
                      type=lambda x: x.lower() == 'true',
                      default=True,
                      help='Show data in console (default: true). Use -v false to disable.')
    parser.add_argument('-d', '--departments', action='store_true',
                      help='Include department names')
    parser.add_argument('-a', '--asset-data', action='store_true',
                      help='Include all asset data (equivalent to using all data options except components)')
    parser.add_argument('-t', '--asset-type', action='store_true',
                      help='Include asset type')
    parser.add_argument('-l', '--location', action='store_true',
                      help='Include location')
    parser.add_argument('-u', '--user', action='store_true',
                      help='Include user information')
    parser.add_argument('-s', '--system-os', action='store_true',
                      help='Include system OS')
    parser.add_argument('-n', '--machine-ip', action='store_true',
                      help='Include machine IP')
    parser.add_argument('-m', '--machine-mac', action='store_true',
                      help='Include MAC address')
    parser.add_argument('-sn', '--serial-number', action='store_true',
                      help='Include serial number')
    parser.add_argument('-desc', '--description', action='store_true',
                      help='Include asset description')
    parser.add_argument('-dj', '--disable-join', action='store_true',
                      help='Disable RAM joining')
    parser.add_argument('-jc', '--combine-cpu-ram', action='store_true',
                      help='Combine CPU and RAM info')
    parser.add_argument('--subdomain',
                      default='gdnt',
                      help='Freshservice subdomain')
    parser.add_argument('--api-key',
                      default='G5omoOghHgcOj2h92in5',
                      help='API key for authentication')
    parser.add_argument('-su', '--search-user', nargs='+',
                      help='Search assets by user full name (e.g. "John Doe")')
    parser.add_argument('-sd', '--search-department',
                      help='Search assets by department name')
    parser.add_argument('-sl', '--search-location',
                      help='Search assets by location name')
    parser.add_argument('-ld', '--list-departments', action='store_true',
                      help='List all available departments')
    parser.add_argument('-ll', '--list-locations', action='store_true',
                      help='List all available locations')
    parser.add_argument('-ie', '--import-excel',
                      help='Import asset IDs from the first column of an Excel file and export to .txt')
    
    return parser.parse_args()

def main():
    """Main execution function"""
    init(autoreset=True, convert=True)  # Asegurar que colorama se inicialice correctamente
    args = parse_arguments()
    
    logger.info("Starting Freshservice Tool")
    logger.debug("Command line arguments: %s", vars(args))
    
    manager = FreshServiceManager()

    if args.components:
        logger.info(f"Component search requested for types: {args.components}")
        logger.debug("Validating component types...")
        valid_components = ['cpu', 'ram', 'hdd', 'nic']
        components = [comp.lower() for comp in args.components]
        invalid_components = [comp for comp in components if comp not in valid_components]
        
        if invalid_components:
            logger.error(f"Invalid component types specified: {invalid_components}")
            logger.debug(f"Valid components are: {valid_components}")
            print(f"{Fore.RED}Error: Invalid component types: {', '.join(invalid_components)}")
            print(f"{Fore.YELLOW}Valid components are: {', '.join(valid_components)}")
            return
        logger.info(f"Component validation successful: {components}")

    if args.import_excel:
        manager.import_excel_ids(args.import_excel)
        return

    # Primero manejar las opciones de búsqueda y listado
    if args.list_departments:
        manager.list_departments()
        return
    elif args.list_locations:
        manager.list_locations()
        return
    elif args.search_user:
        manager.search_by_user(' '.join(args.search_user), args.output)
        return
    elif args.search_department:
        manager.search_by_department(args.search_department, args.output)
        return
    elif args.search_location:
        manager.search_by_location(args.search_location, args.output)
        return

    # Verificar si se proporcionó el argumento ids
    if not args.ids:
        print(f"{Fore.RED}Error: The -i/--ids argument is required when not using search options.")
        return
    
    # Procesar opciones
    options = {
        'ids': args.ids,
        'exclude': args.exclude,
        'components': args.components,
        'output': args.output,
        'verbose': args.verbose,
        'asset_data': args.asset_data,
        'include_departments': args.departments or args.asset_data,
        'include_asset_type': args.asset_type or args.asset_data,
        'include_location': args.location or args.asset_data,
        'include_user': args.user or args.asset_data,
        'include_system_os': args.system_os or args.asset_data,
        'include_machine_ip': args.machine_ip or args.asset_data,
        'include_machine_mac': args.machine_mac or args.asset_data,
        'include_serial_number': args.serial_number or args.asset_data,
        'include_description': args.description or args.asset_data,
        'disable_join': args.disable_join,
        'combine_cpu_ram': args.combine_cpu_ram
    }
    
    logger.debug("Processing with options: %s", options)
    try:
        manager.run(options)
        logger.info("Processing completed successfully")
    except Exception as e:
        logger.exception("Error during processing")
        print(f"{Fore.RED}Error: {str(e)}")

if __name__ == "__main__":
    main()